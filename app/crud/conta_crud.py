"""Contas (sessoes de atendimento), pagamentos e cobrancas PIX."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core import realtime
from app.core.errors import BusinessRuleError, ConflictError, NotFoundError
from app.core.pix import gerar_br_code
from app.core.utils import novo_token, q2, utcnow
from app.models.models import (
    STATUS_SESSAO_ABERTA,
    CategoriaFinanceira,
    CobrancaPix,
    Estabelecimento,
    ItemPedido,
    Mesa,
    MovimentacaoFinanceira,
    Pagamento,
    Pedido,
    SessaoAtendimento,
)

PEDIDOS_EM_ANDAMENTO = ('recebido', 'em_preparo', 'pronto')


def _query_sessao():
    return select(SessaoAtendimento).options(
        selectinload(SessaoAtendimento.mesa),
        selectinload(SessaoAtendimento.pedidos)
        .selectinload(Pedido.itens)
        .selectinload(ItemPedido.menu),
        selectinload(SessaoAtendimento.pagamentos),
    )


def get_sessao(db: Session, id_estab: int, sessao_id: int):
    sessao = db.scalar(
        _query_sessao().where(
            SessaoAtendimento.id == sessao_id,
            SessaoAtendimento.id_estabelecimento == id_estab,
        )
    )
    if not sessao:
        raise NotFoundError('Conta nao encontrada')
    return sessao


def list_sessoes(
    db: Session, id_estab: int, status: list[str] | None = None, limite=200
):
    q = _query_sessao().where(SessaoAtendimento.id_estabelecimento == id_estab)
    if status:
        q = q.where(SessaoAtendimento.status.in_(status))
    return db.scalars(
        q.order_by(SessaoAtendimento.aberta_em.desc()).limit(limite)
    ).all()


def abrir_sessao(
    db: Session, id_estab: int, mesa: Mesa | None, tipo: str, cliente_nome
):
    if mesa is not None:
        tipo = 'mesa'
    elif tipo == 'mesa':
        raise BusinessRuleError('Informe a mesa para uma conta do tipo mesa')
    sessao = SessaoAtendimento(
        id_estabelecimento=id_estab,
        id_mesa=mesa.id if mesa else None,
        tipo=tipo,
        cliente_nome=cliente_nome,
        status='aberta',
        desconto=Decimal('0'),
        acrescimo=Decimal('0'),
    )
    db.add(sessao)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError('Esta mesa ja possui uma conta aberta') from exc
    return sessao


def obter_ou_abrir_sessao_mesa(db: Session, id_estab: int, mesa: Mesa):
    if mesa.id_estabelecimento != id_estab or not mesa.ativo:
        raise BusinessRuleError('Mesa invalida ou desativada')
    sessao = db.scalar(
        select(SessaoAtendimento).where(
            SessaoAtendimento.id_mesa == mesa.id,
            SessaoAtendimento.status.in_(STATUS_SESSAO_ABERTA),
        )
    )
    return sessao or abrir_sessao(db, id_estab, mesa, 'mesa', None)


def resumo(sessao: SessaoAtendimento) -> dict:
    """Calcula a conta a partir dos valores persistidos no banco."""
    subtotal = q2(
        sum(
            (
                item.subtotal
                for p in sessao.pedidos
                if p.status != 'cancelado'
                for item in p.itens
                if item.status != 'cancelado'
            ),
            start=Decimal('0'),
        )
    )
    desconto = q2(sessao.desconto)
    acrescimo = q2(sessao.acrescimo)
    total = q2(max(subtotal - desconto + acrescimo, Decimal('0')))
    pago = q2(
        sum(
            (p.valor for p in sessao.pagamentos if p.status == 'confirmado'),
            start=Decimal('0'),
        )
    )
    return {
        'subtotal': subtotal,
        'desconto': desconto,
        'acrescimo': acrescimo,
        'total': total,
        'total_pago': pago,
        'saldo': q2(total - pago),
    }


def sessao_to_dict(sessao: SessaoAtendimento) -> dict:
    return {
        'id': sessao.id,
        'tipo': sessao.tipo,
        'status': sessao.status,
        'id_mesa': sessao.id_mesa,
        'mesa_numero': sessao.mesa.numero if sessao.mesa else None,
        'cliente_nome': sessao.cliente_nome,
        'aberta_em': sessao.aberta_em,
        'encerrada_em': sessao.encerrada_em,
        'motivo_desconto': sessao.motivo_desconto,
        'motivo_acrescimo': sessao.motivo_acrescimo,
        'resumo': resumo(sessao),
    }


def _exigir_aberta(sessao: SessaoAtendimento):
    if sessao.status not in STATUS_SESSAO_ABERTA:
        raise BusinessRuleError('A conta ja foi encerrada ou cancelada')


def ajustar_conta(db: Session, estab: Estabelecimento, sessao_id: int, data):
    sessao = get_sessao(db, estab.id, sessao_id)
    _exigir_aberta(sessao)
    if data.aplicar_taxa_servico:
        pct = q2(estab.taxa_servico_percentual)
        sessao.acrescimo = q2(resumo(sessao)['subtotal'] * pct / 100)
        sessao.motivo_acrescimo = f'Taxa de servico {pct}%'
    if data.acrescimo is not None:
        sessao.acrescimo = q2(data.acrescimo)
        sessao.motivo_acrescimo = data.motivo_acrescimo
    if data.desconto is not None:
        if data.desconto > 0 and not data.motivo_desconto:
            raise BusinessRuleError('Informe o motivo do desconto')
        sessao.desconto = q2(data.desconto)
        sessao.motivo_desconto = data.motivo_desconto

    r = resumo(sessao)
    if sessao.desconto > r['subtotal'] + r['acrescimo']:
        db.rollback()
        raise BusinessRuleError('Desconto maior que o valor da conta')
    if r['saldo'] < 0:
        db.rollback()
        raise BusinessRuleError(
            'O ajuste deixaria a conta com valor menor que o ja pago'
        )
    db.commit()
    return get_sessao(db, estab.id, sessao_id)


def solicitar_fechamento(db: Session, id_estab: int, sessao_id: int):
    sessao = get_sessao(db, id_estab, sessao_id)
    _exigir_aberta(sessao)
    sessao.status = 'aguardando_pagamento'
    db.commit()
    realtime.notificar(id_estab)
    return get_sessao(db, id_estab, sessao_id)


def encerrar_sessao(db: Session, id_estab: int, sessao_id: int):
    sessao = get_sessao(db, id_estab, sessao_id)
    _exigir_aberta(sessao)
    if any(p.status in PEDIDOS_EM_ANDAMENTO for p in sessao.pedidos):
        raise BusinessRuleError(
            'Existem pedidos ainda nao entregues nesta conta'
        )
    r = resumo(sessao)
    if r['saldo'] > 0:
        raise BusinessRuleError(
            f'A conta ainda possui saldo pendente de R$ {r["saldo"]}'
        )
    sessao.status = 'encerrada'
    sessao.encerrada_em = utcnow()
    db.commit()
    realtime.notificar(id_estab)
    return get_sessao(db, id_estab, sessao_id)


def cancelar_sessao(db: Session, id_estab: int, sessao_id: int):
    sessao = get_sessao(db, id_estab, sessao_id)
    _exigir_aberta(sessao)
    if any(p.status != 'cancelado' for p in sessao.pedidos):
        raise BusinessRuleError(
            'So e possivel cancelar contas sem pedidos ativos'
        )
    if any(p.status == 'confirmado' for p in sessao.pagamentos):
        raise BusinessRuleError('A conta possui pagamentos; estorne antes')
    sessao.status = 'cancelada'
    sessao.encerrada_em = utcnow()
    db.commit()
    realtime.notificar(id_estab)
    return get_sessao(db, id_estab, sessao_id)


def _categoria_vendas(db: Session, id_estab: int) -> CategoriaFinanceira:
    cat = db.scalar(
        select(CategoriaFinanceira).where(
            CategoriaFinanceira.id_estabelecimento == id_estab,
            CategoriaFinanceira.tipo == 'entrada',
            CategoriaFinanceira.sistema.is_(True),
        )
    )
    if not cat:
        cat = CategoriaFinanceira(
            id_estabelecimento=id_estab,
            nome='Vendas',
            tipo='entrada',
            sistema=True,
        )
        db.add(cat)
        db.flush()
    return cat


def registrar_pagamento(
    db: Session,
    id_estab: int,
    sessao_id: int,
    data,
    user_id: int,
    id_pedido: int | None = None,
) -> tuple[Pagamento, bool]:
    """Registra um pagamento manual. Retorna (pagamento, criado)."""
    existente = db.scalar(
        select(Pagamento).where(
            Pagamento.id_estabelecimento == id_estab,
            Pagamento.chave_idempotencia == data.chave_idempotencia,
        )
    )
    if existente:
        if existente.id_sessao != sessao_id:
            raise ConflictError('Chave de idempotencia ja utilizada')
        return existente, False

    sessao = get_sessao(db, id_estab, sessao_id)
    _exigir_aberta(sessao)
    valor = q2(data.valor)
    saldo = resumo(sessao)['saldo']
    if saldo <= 0:
        raise BusinessRuleError('A conta nao possui saldo a pagar')
    if valor > saldo:
        raise BusinessRuleError(
            f'Valor maior que o saldo da conta (R$ {saldo}). '
            'Registre apenas o valor devido; o troco e calculado no caixa.'
        )

    pagamento = Pagamento(
        id_estabelecimento=id_estab,
        id_sessao=sessao.id,
        id_pedido=id_pedido,
        valor=valor,
        metodo=data.metodo,
        status='confirmado',
        origem='manual',
        chave_idempotencia=data.chave_idempotencia,
        observacao=data.observacao,
        id_usuario=user_id,
        data_hora=utcnow(),
    )
    db.add(pagamento)
    try:
        db.flush()
        # Receita entra no financeiro somente quando ha recebimento
        mesa = f'mesa {sessao.mesa.numero}' if sessao.mesa else sessao.tipo
        ref = f'pedido #{id_pedido}' if id_pedido else f'conta #{sessao.id}'
        db.add(
            MovimentacaoFinanceira(
                id_estabelecimento=id_estab,
                tipo='entrada',
                descricao=f'Recebimento {ref} ({mesa})',
                id_categoria=_categoria_vendas(db, id_estab).id,
                valor=valor,
                data_hora=pagamento.data_hora,
                metodo_pagamento=data.metodo,
                id_usuario=user_id,
                id_pagamento=pagamento.id,
            )
        )
        if data.metodo == 'pix':
            pix = db.scalar(
                select(CobrancaPix).where(
                    CobrancaPix.id_sessao == sessao.id,
                    CobrancaPix.status == 'pendente',
                    CobrancaPix.valor == valor,
                )
            )
            if pix:
                pix.status = 'paga'
                pix.id_pagamento = pagamento.id
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        repetido = db.scalar(
            select(Pagamento).where(
                Pagamento.id_estabelecimento == id_estab,
                Pagamento.chave_idempotencia == data.chave_idempotencia,
            )
        )
        if repetido:
            return repetido, False
        raise ConflictError('Nao foi possivel registrar o pagamento') from exc
    db.refresh(pagamento)
    realtime.notificar(id_estab)
    return pagamento, True


def estornar_pagamento(
    db: Session, id_estab: int, pagamento_id: int, motivo: str, user_id: int
):
    pagamento = db.get(Pagamento, pagamento_id)
    if not pagamento or pagamento.id_estabelecimento != id_estab:
        raise NotFoundError('Pagamento nao encontrado')
    if pagamento.status == 'estornado':
        raise BusinessRuleError('Pagamento ja estornado')
    _exigir_aberta(pagamento.sessao)

    agora = utcnow()
    pagamento.status = 'estornado'
    pagamento.estornado_em = agora
    pagamento.motivo_estorno = motivo
    mov = db.scalar(
        select(MovimentacaoFinanceira).where(
            MovimentacaoFinanceira.id_pagamento == pagamento.id
        )
    )
    if mov and mov.status == 'ativa':
        mov.status = 'cancelada'
        mov.cancelado_em = agora
        mov.motivo_cancelamento = f'Estorno do pagamento: {motivo}'
        mov.id_usuario_cancelamento = user_id
    db.commit()
    db.refresh(pagamento)
    return pagamento


def gerar_cobranca_pix(
    db: Session, estab: Estabelecimento, sessao_id: int, valor
) -> CobrancaPix:
    sessao = get_sessao(db, estab.id, sessao_id)
    _exigir_aberta(sessao)
    saldo = resumo(sessao)['saldo']
    valor = q2(valor) if valor else saldo
    if valor <= 0 or valor > saldo:
        raise BusinessRuleError(f'Valor invalido. Saldo da conta: R$ {saldo}')

    txid = f'S{sessao.id}{novo_token(8)}'
    txid = ''.join(c for c in txid if c.isalnum())[:25]
    cobranca = CobrancaPix(
        id_estabelecimento=estab.id,
        id_sessao=sessao.id,
        txid=txid,
        valor=valor,
        copia_e_cola=gerar_br_code(
            estab.chave_pix, estab.nome_titular, estab.cidade, valor, txid
        ),
        provedor='estatico',
        status='pendente',
    )
    db.add(cobranca)
    db.commit()
    db.refresh(cobranca)
    return cobranca


def list_cobrancas(db: Session, id_estab: int, sessao_id: int):
    return db.scalars(
        select(CobrancaPix)
        .where(
            CobrancaPix.id_estabelecimento == id_estab,
            CobrancaPix.id_sessao == sessao_id,
        )
        .order_by(CobrancaPix.id.desc())
    ).all()
