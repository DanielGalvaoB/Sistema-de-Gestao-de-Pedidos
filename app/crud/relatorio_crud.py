"""Relatorios financeiros.

Criterios (nao misturados):
- Vendas: itens nao cancelados de pedidos nao cancelados, pela data do
  pedido. Valor bruto dos itens (descontos/acrescimos ficam na conta).
- Recebido: pagamentos confirmados (nao estornados), pela data do pagamento.
- Entradas/Despesas: movimentacoes financeiras ativas, pela data da
  movimentacao. Entradas incluem os recebimentos de vendas (lancados
  automaticamente) e receitas adicionais.
- Pendente: saldo das contas ainda abertas que foram abertas no periodo.
"""

import csv
import io
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.utils import periodo_utc, q2, to_local
from app.crud import conta_crud
from app.crud.financeiro_crud import list_movimentacoes, mov_to_dict
from app.models.models import (
    STATUS_SESSAO_ABERTA,
    Pagamento,
    Pedido,
    SessaoAtendimento,
)

CRITERIOS = {
    'vendas': 'Itens nao cancelados, pela data do pedido (valor bruto)',
    'recebido': 'Pagamentos confirmados, pela data do pagamento',
    'despesas': 'Saidas ativas, pela data da movimentacao',
    'entradas': 'Entradas ativas (inclui recebimentos), pela data da '
    'movimentacao',
    'saldo': 'Entradas menos saidas no periodo',
    'pendente': 'Saldo das contas abertas no periodo e ainda nao quitadas',
}

ZERO = Decimal('0')
_NL = {'new_x': XPos.LMARGIN, 'new_y': YPos.NEXT}


def resumo(
    db: Session,
    id_estab: int,
    inicio: date,
    fim: date,
    metodo: str | None = None,
    id_categoria: int | None = None,
) -> dict:
    ini, end = periodo_utc(inicio, fim)
    dias = {
        inicio + timedelta(days=i): {
            'vendas': ZERO,
            'recebido': ZERO,
            'despesas': ZERO,
        }
        for i in range((fim - inicio).days + 1)
    }

    # Vendas
    pedidos = db.scalars(
        select(Pedido)
        .options(selectinload(Pedido.itens))
        .where(
            Pedido.id_estabelecimento == id_estab,
            Pedido.status != 'cancelado',
            Pedido.created_at >= ini,
            Pedido.created_at < end,
        )
    ).all()
    total_vendas = ZERO
    produtos: dict[str, list] = defaultdict(lambda: [ZERO, 0])
    for p in pedidos:
        valor_pedido = ZERO
        for item in p.itens:
            if item.status == 'cancelado':
                continue
            valor_pedido += item.subtotal
            produtos[item.nome_produto][0] += item.subtotal
            produtos[item.nome_produto][1] += item.quantidade
        total_vendas += valor_pedido
        dia = to_local(p.created_at).date()
        if dia in dias:
            dias[dia]['vendas'] += valor_pedido
    qtd_pedidos = len(pedidos)

    # Recebimentos
    q_pag = select(Pagamento).where(
        Pagamento.id_estabelecimento == id_estab,
        Pagamento.status == 'confirmado',
        Pagamento.data_hora >= ini,
        Pagamento.data_hora < end,
    )
    if metodo:
        q_pag = q_pag.where(Pagamento.metodo == metodo)
    total_recebido = ZERO
    por_metodo: dict[str, list] = defaultdict(lambda: [ZERO, 0])
    for pag in db.scalars(q_pag):
        total_recebido += pag.valor
        por_metodo[pag.metodo][0] += pag.valor
        por_metodo[pag.metodo][1] += 1
        dia = to_local(pag.data_hora).date()
        if dia in dias:
            dias[dia]['recebido'] += pag.valor

    # Movimentacoes
    movs = list_movimentacoes(
        db,
        id_estab,
        ini,
        end,
        status='ativa',
        id_categoria=id_categoria,
        metodo=metodo,
    )
    total_entradas = ZERO
    total_despesas = ZERO
    por_categoria: dict[str, list] = defaultdict(lambda: [ZERO, 0])
    for m in movs:
        if m.tipo == 'entrada':
            total_entradas += m.valor
        else:
            total_despesas += m.valor
            por_categoria[m.categoria.nome][0] += m.valor
            por_categoria[m.categoria.nome][1] += 1
            dia = to_local(m.data_hora).date()
            if dia in dias:
                dias[dia]['despesas'] += m.valor

    # Pendente
    sessoes = db.scalars(
        select(SessaoAtendimento)
        .options(
            selectinload(SessaoAtendimento.pedidos).selectinload(Pedido.itens),
            selectinload(SessaoAtendimento.pagamentos),
        )
        .where(
            SessaoAtendimento.id_estabelecimento == id_estab,
            SessaoAtendimento.status.in_(STATUS_SESSAO_ABERTA),
            SessaoAtendimento.aberta_em >= ini,
            SessaoAtendimento.aberta_em < end,
        )
    ).all()
    pendente = sum(
        (max(conta_crud.resumo(s)['saldo'], ZERO) for s in sessoes),
        start=ZERO,
    )

    def _rank(d, limite=10):
        itens = sorted(d.items(), key=lambda kv: kv[1][0], reverse=True)
        return [
            {'rotulo': k, 'valor': q2(v[0]), 'quantidade': v[1]}
            for k, v in itens[:limite]
        ]

    top_produtos = sorted(
        produtos.items(), key=lambda kv: kv[1][1], reverse=True
    )[:10]
    return {
        'inicio': inicio,
        'fim': fim,
        'criterios': CRITERIOS,
        'total_vendas': q2(total_vendas),
        'total_recebido': q2(total_recebido),
        'total_entradas': q2(total_entradas),
        'total_despesas': q2(total_despesas),
        'saldo': q2(total_entradas - total_despesas),
        'pendente_recebimento': q2(pendente),
        'quantidade_pedidos': qtd_pedidos,
        'ticket_medio': q2(total_vendas / qtd_pedidos)
        if qtd_pedidos
        else q2(0),
        'produtos_mais_vendidos': [
            {'rotulo': k, 'valor': q2(v[0]), 'quantidade': v[1]}
            for k, v in top_produtos
        ],
        'vendas_por_dia': [
            {
                'dia': d,
                'vendas': q2(v['vendas']),
                'recebido': q2(v['recebido']),
                'despesas': q2(v['despesas']),
            }
            for d, v in sorted(dias.items())
        ],
        'recebido_por_metodo': _rank(por_metodo),
        'despesas_por_categoria': _rank(por_categoria),
    }


def _linhas_extrato(db, id_estab, inicio, fim, **filtros):
    ini, end = periodo_utc(inicio, fim)
    movs = list_movimentacoes(db, id_estab, ini, end, **filtros)
    return [mov_to_dict(m) for m in movs]


def extrato_csv(db, id_estab, inicio, fim, **filtros) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=';')
    w.writerow([
        'id',
        'data_hora',
        'tipo',
        'categoria',
        'descricao',
        'metodo',
        'valor',
        'status',
        'origem',
    ])
    for m in _linhas_extrato(db, id_estab, inicio, fim, **filtros):
        w.writerow([
            m['id'],
            to_local(m['data_hora']).strftime('%d/%m/%Y %H:%M'),
            m['tipo'],
            m['categoria_nome'],
            m['descricao'],
            m['metodo_pagamento'] or '',
            str(q2(m['valor'])).replace('.', ','),
            m['status'],
            'pagamento' if m['automatica'] else 'manual',
        ])
    # BOM para o Excel abrir com acentuacao correta
    return '﻿' + buf.getvalue()


def _latin1(txt: str) -> str:
    return str(txt).encode('latin-1', 'replace').decode('latin-1')


def extrato_pdf(db, id_estab, nome_loja, inicio, fim, **filtros) -> bytes:
    linhas = _linhas_extrato(db, id_estab, inicio, fim, **filtros)
    res = resumo(db, id_estab, inicio, fim)
    pdf = FPDF(orientation='L', format='A4')
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 8, _latin1(f'Extrato financeiro - {nome_loja}'), **_NL)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(
        0,
        6,
        f'Periodo: {inicio:%d/%m/%Y} a {fim:%d/%m/%Y}',
        **_NL,
    )
    pdf.cell(
        0,
        6,
        _latin1(
            f'Vendas: R$ {res["total_vendas"]}   Recebido: R$ '
            f'{res["total_recebido"]}   Entradas: R$ {res["total_entradas"]}'
            f'   Despesas: R$ {res["total_despesas"]}   Saldo: R$ '
            f'{res["saldo"]}'
        ),
        **_NL,
    )
    pdf.ln(2)
    cols = [
        ('Data', 30),
        ('Tipo', 18),
        ('Categoria', 45),
        ('Descricao', 95),
        ('Metodo', 30),
        ('Valor', 28),
        ('Status', 24),
    ]
    pdf.set_font('Helvetica', 'B', 9)
    for titulo, larg in cols:
        pdf.cell(larg, 7, titulo, border=1)
    pdf.ln()
    pdf.set_font('Helvetica', '', 8)
    for m in linhas:
        valores = [
            to_local(m['data_hora']).strftime('%d/%m/%Y %H:%M'),
            m['tipo'],
            m['categoria_nome'][:28],
            m['descricao'][:62],
            m['metodo_pagamento'] or '',
            f'{q2(m["valor"])}',
            m['status'],
        ]
        for (_, larg), v in zip(cols, valores):
            pdf.cell(larg, 6, _latin1(v), border=1)
        pdf.ln()
    return bytes(pdf.output())
