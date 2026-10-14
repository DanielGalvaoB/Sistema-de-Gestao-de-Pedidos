from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core import realtime
from app.core.errors import BusinessRuleError, NotFoundError
from app.core.utils import novo_token, q2, utcnow
from app.crud import conta_crud
from app.models.models import (
    Estabelecimento,
    HistoricoStatusPedido,
    ItemPedido,
    Menu,
    Pedido,
    SessaoAtendimento,
)

ATIVOS_COZINHA = ('recebido', 'em_preparo', 'pronto')
FINAIS = ('entregue', 'cancelado')

# Transicoes permitidas para um item
TRANSICOES_ITEM = {
    'recebido': {'em_preparo', 'pronto', 'cancelado'},
    'em_preparo': {'recebido', 'pronto', 'cancelado'},
    'pronto': {'em_preparo', 'entregue', 'cancelado'},
    'entregue': set(),
    'cancelado': set(),
}
# Transicoes permitidas para o pedido como um todo
TRANSICOES_PEDIDO = {
    'recebido': {'em_preparo', 'pronto', 'cancelado'},
    'em_preparo': {'pronto', 'cancelado'},
    'pronto': {'entregue', 'cancelado'},
    'entregue': set(),
    'cancelado': set(),
}


def _query_pedidos():
    return select(Pedido).options(
        selectinload(Pedido.itens).selectinload(ItemPedido.menu),
        selectinload(Pedido.sessao).selectinload(SessaoAtendimento.mesa),
    )


def _tempo_item(item: ItemPedido, estab: Estabelecimento) -> int:
    return item.menu.tempo_preparo_min or estab.tempo_preparo_padrao_min


def total_pedido(pedido: Pedido) -> object:
    if pedido.status == 'cancelado':
        return q2(0)
    return q2(
        sum(
            (i.subtotal for i in pedido.itens if i.status != 'cancelado'),
            start=q2(0),
        )
    )


def pedido_to_dict(
    pedido: Pedido,
    estab: Estabelecimento,
    agora: datetime | None = None,
    com_historico: bool = False,
) -> dict:
    agora = agora or utcnow()
    em_aberto = pedido.status in {'recebido', 'em_preparo'}
    atrasado, minutos_atraso, alerta = False, 0, False
    if em_aberto and pedido.previsao_pronto:
        if agora > pedido.previsao_pronto:
            atrasado = True
            minutos_atraso = int(
                (agora - pedido.previsao_pronto).total_seconds() // 60
            )
        else:
            duracao = (
                pedido.previsao_pronto - pedido.created_at
            ).total_seconds()
            decorrido = (agora - pedido.created_at).total_seconds()
            limite = duracao * estab.alerta_atraso_percentual / 100
            alerta = duracao > 0 and decorrido >= limite

    itens = []
    for item in pedido.itens:
        previsao_item = pedido.created_at + timedelta(
            minutes=_tempo_item(item, estab)
        )
        item_atrasado = (
            item.status in {'recebido', 'em_preparo'} and agora > previsao_item
        )
        itens.append({
            'id': item.id,
            'id_menu': item.id_menu,
            'nome_produto': item.nome_produto,
            'preco_unitario': item.preco_unitario,
            'quantidade': item.quantidade,
            'subtotal': item.subtotal,
            'observacao': item.observacao,
            'status': item.status,
            'iniciado_em': item.iniciado_em,
            'pronto_em': item.pronto_em,
            'previsao_pronto': previsao_item,
            'atrasado': item_atrasado,
        })

    sessao = pedido.sessao
    return {
        'id': pedido.id,
        'id_sessao': pedido.id_sessao,
        'status': pedido.status,
        'observacao': pedido.observacao,
        'origem': pedido.origem,
        'codigo_acompanhamento': pedido.codigo_acompanhamento,
        'created_at': pedido.created_at,
        'iniciado_em': pedido.iniciado_em,
        'pronto_em': pedido.pronto_em,
        'entregue_em': pedido.entregue_em,
        'cancelado_em': pedido.cancelado_em,
        'previsao_pronto': pedido.previsao_pronto,
        'motivo_atraso': pedido.motivo_atraso,
        'motivo_cancelamento': pedido.motivo_cancelamento,
        'total': total_pedido(pedido),
        'tipo_atendimento': sessao.tipo,
        'mesa_numero': sessao.mesa.numero if sessao.mesa else None,
        'cliente_nome': sessao.cliente_nome,
        'atrasado': atrasado,
        'minutos_atraso': minutos_atraso,
        'alerta_prazo': alerta,
        'itens': itens,
        'historico': pedido.historico if com_historico else [],
    }


def _registrar_historico(
    db, pedido, novo, anterior, user_id=None, item_id=None, motivo=None
):
    db.add(
        HistoricoStatusPedido(
            id_pedido=pedido.id,
            id_item=item_id,
            status_anterior=anterior,
            status_novo=novo,
            motivo=motivo,
            id_usuario=user_id,
        )
    )


def criar_pedido(
    db: Session,
    estab: Estabelecimento,
    sessao: SessaoAtendimento,
    itens_in,
    observacao: str | None,
    origem: str,
    user_id: int | None = None,
) -> Pedido:
    """Cria o pedido e seus itens numa unica transacao.

    Precos vem sempre do banco; o cliente envia apenas produto e quantidade.
    """
    if sessao.status not in {'aberta', 'aguardando_pagamento'}:
        raise BusinessRuleError('A conta informada nao esta aberta')

    ids = {i.id_menu for i in itens_in}
    produtos = {
        m.id: m
        for m in db.scalars(
            select(Menu).where(
                Menu.id.in_(ids), Menu.id_estabelecimento == estab.id
            )
        )
    }
    for item in itens_in:
        menu = produtos.get(item.id_menu)
        if not menu or not menu.ativo:
            raise BusinessRuleError(f'Produto {item.id_menu} nao encontrado')
        if not menu.is_disponivel:
            raise BusinessRuleError(f'Produto "{menu.nome}" esta indisponivel')
        if item.quantidade <= 0:
            raise BusinessRuleError('Quantidade deve ser maior que zero')

    agora = utcnow()
    tempo = max(
        (
            produtos[i.id_menu].tempo_preparo_min
            or estab.tempo_preparo_padrao_min
        )
        for i in itens_in
    )
    pedido = Pedido(
        id_estabelecimento=estab.id,
        id_sessao=sessao.id,
        status='recebido',
        observacao=observacao,
        origem=origem,
        codigo_acompanhamento=novo_token(16),
        created_at=agora,
        previsao_pronto=agora + timedelta(minutes=tempo),
    )
    for item in itens_in:
        menu = produtos[item.id_menu]
        preco = q2(menu.preco)
        pedido.itens.append(
            ItemPedido(
                id_menu=menu.id,
                nome_produto=menu.nome,
                preco_unitario=preco,
                quantidade=item.quantidade,
                subtotal=q2(preco * item.quantidade),
                observacao=item.observacao,
                status='recebido',
            )
        )
    if sessao.status == 'aguardando_pagamento':
        # Novo consumo reabre a conta
        sessao.status = 'aberta'

    try:
        db.add(pedido)
        db.flush()
        _registrar_historico(db, pedido, 'recebido', None, user_id)
        db.commit()
    except Exception:
        db.rollback()
        raise
    realtime.notificar(estab.id)
    return get_pedido(db, estab.id, pedido.id)


def get_pedido(db: Session, id_estab: int, pedido_id: int) -> Pedido:
    pedido = db.scalar(
        _query_pedidos()
        .options(selectinload(Pedido.historico))
        .where(Pedido.id == pedido_id, Pedido.id_estabelecimento == id_estab)
    )
    if not pedido:
        raise NotFoundError('Pedido nao encontrado')
    return pedido


def get_por_codigo(db: Session, codigo: str) -> Pedido:
    pedido = db.scalar(
        _query_pedidos().where(Pedido.codigo_acompanhamento == codigo)
    )
    if not pedido:
        raise NotFoundError('Pedido nao encontrado')
    return pedido


def list_pedidos(
    db: Session,
    id_estab: int,
    status: list[str] | None = None,
    id_sessao: int | None = None,
    inicio: datetime | None = None,
    fim: datetime | None = None,
    limite: int = 200,
):
    q = _query_pedidos().where(Pedido.id_estabelecimento == id_estab)
    if status:
        q = q.where(Pedido.status.in_(status))
    if id_sessao:
        q = q.where(Pedido.id_sessao == id_sessao)
    if inicio:
        q = q.where(Pedido.created_at >= inicio)
    if fim:
        q = q.where(Pedido.created_at < fim)
    return db.scalars(q.order_by(Pedido.created_at.desc()).limit(limite)).all()


def _aplicar_status_item(item: ItemPedido, novo: str, agora: datetime):
    if novo == 'em_preparo' and not item.iniciado_em:
        item.iniciado_em = agora
    if novo == 'pronto':
        item.iniciado_em = item.iniciado_em or agora
        item.pronto_em = agora
    if novo in {'recebido', 'em_preparo'}:
        item.pronto_em = None
    item.status = novo


def _derivar_status_pedido(pedido: Pedido) -> str:
    ativos = [i.status for i in pedido.itens if i.status != 'cancelado']
    if not ativos:
        return 'cancelado'
    if all(s == 'entregue' for s in ativos):
        return 'entregue'
    if all(s in {'pronto', 'entregue'} for s in ativos):
        return 'pronto'
    if any(s != 'recebido' for s in ativos):
        return 'em_preparo'
    return 'recebido'


def _aplicar_status_pedido(pedido: Pedido, novo: str, agora: datetime):
    pedido.status = novo
    if novo in {'em_preparo', 'pronto'} and not pedido.iniciado_em:
        pedido.iniciado_em = agora
    if novo == 'pronto':
        pedido.pronto_em = agora
    elif novo == 'em_preparo':
        pedido.pronto_em = None
    if novo == 'entregue':
        pedido.entregue_em = agora
    if novo == 'cancelado':
        pedido.cancelado_em = agora


def alterar_status_pedido(
    db: Session, id_estab: int, pedido_id: int, novo: str, motivo, user_id
):
    pedido = get_pedido(db, id_estab, pedido_id)
    anterior = pedido.status
    if novo == anterior:
        return pedido
    if novo not in TRANSICOES_PEDIDO[anterior]:
        raise BusinessRuleError(
            f'Nao e possivel mudar o pedido de "{anterior}" para "{novo}"'
        )
    if novo == 'cancelado' and not motivo:
        raise BusinessRuleError('Informe o motivo do cancelamento')

    agora = utcnow()
    ativos = [i for i in pedido.itens if i.status != 'cancelado']
    if novo == 'entregue':
        pendentes = [
            i for i in ativos if i.status not in {'pronto', 'entregue'}
        ]
        if pendentes:
            raise BusinessRuleError(
                'Ha itens que ainda nao estao prontos; '
                'atualize os itens antes de entregar'
            )
    # Regra explicita: ao marcar o pedido inteiro como "pronto" ou
    # "entregue" a cozinha confirma todos os itens ativos.
    alvo_itens = {
        'em_preparo': ('recebido',),
        'pronto': ('recebido', 'em_preparo'),
        'entregue': ('pronto',),
        'cancelado': ('recebido', 'em_preparo', 'pronto'),
    }[novo]
    for item in ativos:
        if item.status in alvo_itens:
            _registrar_historico(
                db, pedido, novo, item.status, user_id, item.id, motivo
            )
            _aplicar_status_item(item, novo, agora)

    _aplicar_status_pedido(pedido, novo, agora)
    if novo == 'cancelado':
        pedido.motivo_cancelamento = motivo
    _registrar_historico(db, pedido, novo, anterior, user_id, motivo=motivo)
    db.commit()
    realtime.notificar(id_estab)
    return get_pedido(db, id_estab, pedido_id)


def alterar_status_item(
    db: Session, id_estab: int, pedido_id: int, item_id: int, novo, motivo, uid
):
    pedido = get_pedido(db, id_estab, pedido_id)
    item = next((i for i in pedido.itens if i.id == item_id), None)
    if not item:
        raise NotFoundError('Item nao encontrado neste pedido')
    anterior = item.status
    if novo == anterior:
        return pedido
    if novo not in TRANSICOES_ITEM[anterior]:
        raise BusinessRuleError(
            f'Nao e possivel mudar o item de "{anterior}" para "{novo}"'
        )
    agora = utcnow()
    _aplicar_status_item(item, novo, agora)
    _registrar_historico(db, pedido, novo, anterior, uid, item.id, motivo)

    derivado = _derivar_status_pedido(pedido)
    if derivado != pedido.status:
        _registrar_historico(db, pedido, derivado, pedido.status, uid)
        _aplicar_status_pedido(pedido, derivado, agora)
        if derivado == 'cancelado':
            pedido.motivo_cancelamento = motivo or 'Todos os itens cancelados'
    db.commit()
    realtime.notificar(id_estab)
    return get_pedido(db, id_estab, pedido_id)


def atualizar_previsao(db: Session, id_estab: int, pedido_id: int, data, uid):
    pedido = get_pedido(db, id_estab, pedido_id)
    if pedido.status in FINAIS or pedido.status == 'pronto':
        raise BusinessRuleError('Pedido ja concluido; previsao nao se aplica')
    if data.previsao_pronto:
        nova = data.previsao_pronto
        if nova.tzinfo is not None:
            # Armazenamos sempre em UTC sem tzinfo
            nova = nova.astimezone(timezone.utc).replace(tzinfo=None)
    elif data.minutos_adicionais:
        base = max(pedido.previsao_pronto or utcnow(), utcnow())
        nova = base + timedelta(minutes=data.minutos_adicionais)
    else:
        raise BusinessRuleError(
            'Informe previsao_pronto ou minutos_adicionais'
        )
    pedido.previsao_pronto = nova
    if data.motivo_atraso:
        pedido.motivo_atraso = data.motivo_atraso
    _registrar_historico(
        db,
        pedido,
        pedido.status,
        pedido.status,
        uid,
        motivo=f'Nova previsao. {data.motivo_atraso or ""}'.strip(),
    )
    db.commit()
    realtime.notificar(id_estab)
    return get_pedido(db, id_estab, pedido_id)


def abrir_sessao_para_pedido(
    db, estab, id_sessao=None, mesa=None, tipo=None, cliente_nome=None
):
    if id_sessao:
        return conta_crud.get_sessao(db, estab.id, id_sessao)
    if mesa is not None:
        return conta_crud.obter_ou_abrir_sessao_mesa(db, estab.id, mesa)
    return conta_crud.abrir_sessao(
        db, estab.id, None, tipo or 'balcao', cliente_nome
    )
