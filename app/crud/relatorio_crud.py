"""Relatorios de vendas e recebimentos.

O sistema controla apenas o que entra; gastos do estabelecimento nao fazem
parte dele. Criterios (nao misturados):
- Vendas: itens nao cancelados de pedidos nao cancelados, pela data do
  pedido. Valor bruto dos itens (descontos/acrescimos ficam na conta).
- Recebido: pagamentos confirmados (nao estornados), pela data do pagamento.
- Outras entradas: entradas manuais ativas, pela data do lancamento.
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
    'outras_entradas': 'Entradas manuais ativas, pela data do lancamento',
    'total_entradas': 'Recebido mais outras entradas',
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
) -> dict:
    ini, end = periodo_utc(inicio, fim)
    dias = {
        inicio + timedelta(days=i): {'vendas': ZERO, 'recebido': ZERO}
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

    # Recebimentos dos pedidos
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

    # Outras entradas (lancamentos manuais, sem pagamento de pedido)
    outras = sum(
        (
            m.valor
            for m in list_movimentacoes(
                db, id_estab, ini, end, status='ativa', metodo=metodo
            )
            if m.id_pagamento is None
        ),
        start=ZERO,
    )

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

    def _rank(d, chave=0, limite=10):
        itens = sorted(d.items(), key=lambda kv: kv[1][chave], reverse=True)
        return [
            {'rotulo': k, 'valor': q2(v[0]), 'quantidade': v[1]}
            for k, v in itens[:limite]
        ]

    return {
        'inicio': inicio,
        'fim': fim,
        'criterios': CRITERIOS,
        'total_vendas': q2(total_vendas),
        'total_recebido': q2(total_recebido),
        'outras_entradas': q2(outras),
        'total_entradas': q2(total_recebido + outras),
        'pendente_recebimento': q2(pendente),
        'quantidade_pedidos': qtd_pedidos,
        'ticket_medio': q2(total_vendas / qtd_pedidos)
        if qtd_pedidos
        else q2(0),
        'produtos_mais_vendidos': _rank(produtos, chave=1),
        'vendas_por_dia': [
            {
                'dia': d,
                'vendas': q2(v['vendas']),
                'recebido': q2(v['recebido']),
            }
            for d, v in sorted(dias.items())
        ],
        'recebido_por_metodo': _rank(por_metodo),
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
    pdf.cell(0, 8, _latin1(f'Extrato de recebimentos - {nome_loja}'), **_NL)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, f'Periodo: {inicio:%d/%m/%Y} a {fim:%d/%m/%Y}', **_NL)
    pdf.cell(
        0,
        6,
        _latin1(
            f'Vendas: R$ {res["total_vendas"]}   Recebido: R$ '
            f'{res["total_recebido"]}   Outras entradas: R$ '
            f'{res["outras_entradas"]}   A receber: R$ '
            f'{res["pendente_recebimento"]}'
        ),
        **_NL,
    )
    pdf.ln(2)
    cols = [
        ('Data', 32),
        ('Categoria', 45),
        ('Descricao', 110),
        ('Metodo', 32),
        ('Valor', 30),
        ('Status', 26),
    ]
    pdf.set_font('Helvetica', 'B', 9)
    for titulo, larg in cols:
        pdf.cell(larg, 7, titulo, border=1)
    pdf.ln()
    pdf.set_font('Helvetica', '', 8)
    for m in linhas:
        valores = [
            to_local(m['data_hora']).strftime('%d/%m/%Y %H:%M'),
            m['categoria_nome'][:28],
            m['descricao'][:72],
            m['metodo_pagamento'] or '',
            f'{q2(m["valor"])}',
            m['status'],
        ]
        for (_, larg), v in zip(cols, valores):
            pdf.cell(larg, 6, _latin1(v), border=1)
        pdf.ln()
    return bytes(pdf.output())
