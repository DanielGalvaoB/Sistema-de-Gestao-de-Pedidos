from datetime import date

from fastapi import APIRouter, Query, status

from app.core.errors import BusinessRuleError
from app.core.utils import periodo_utc
from app.crud import mesa_crud, pedido_crud
from app.dependencies.auth_dep import Atendimento, Cozinha, DbSession
from app.schemas.pedido_schema import (
    PedidoCreate,
    PedidoDetalhe,
    PedidoResponse,
    PrevisaoUpdate,
    StatusUpdate,
)

router = APIRouter(prefix='/pedidos', tags=['pedidos'])


@router.post(
    '/', response_model=PedidoResponse, status_code=status.HTTP_201_CREATED
)
def create_pedido(pedido: PedidoCreate, db: DbSession, user: Atendimento):
    estab = user.estabelecimento
    mesa = None
    if pedido.id_mesa is not None:
        mesa = mesa_crud.get_mesa(db, estab.id, pedido.id_mesa)
    elif pedido.tipo == 'mesa' and pedido.id_sessao is None:
        raise BusinessRuleError('Informe a mesa ou a conta do pedido')
    sessao = pedido_crud.abrir_sessao_para_pedido(
        db,
        estab,
        id_sessao=pedido.id_sessao,
        mesa=mesa,
        tipo=pedido.tipo,
        cliente_nome=pedido.cliente_nome,
    )
    novo = pedido_crud.criar_pedido(
        db,
        estab,
        sessao,
        pedido.itens,
        pedido.observacao,
        origem='equipe',
        user_id=user.id,
    )
    return pedido_crud.pedido_to_dict(novo, estab)


@router.get('/', response_model=list[PedidoResponse])
def list_pedidos(
    db: DbSession,
    user: Cozinha,
    status_: list[str] | None = Query(default=None, alias='status'),
    ativos: bool = False,
    id_sessao: int | None = None,
    inicio: date | None = None,
    fim: date | None = None,
):
    """`ativos=true` retorna recebido/em_preparo/pronto (painel da cozinha)."""
    if ativos:
        status_ = list(pedido_crud.ATIVOS_COZINHA)
    ini = end = None
    if inicio and fim:
        ini, end = periodo_utc(inicio, fim)
    estab = user.estabelecimento
    pedidos = pedido_crud.list_pedidos(
        db, estab.id, status_, id_sessao, ini, end
    )
    return [pedido_crud.pedido_to_dict(p, estab) for p in pedidos]


@router.get('/{pedido_id}', response_model=PedidoDetalhe)
def get_pedido(pedido_id: int, db: DbSession, user: Cozinha):
    estab = user.estabelecimento
    pedido = pedido_crud.get_pedido(db, estab.id, pedido_id)
    return pedido_crud.pedido_to_dict(pedido, estab, com_historico=True)


@router.patch('/{pedido_id}/status', response_model=PedidoResponse)
def alterar_status(
    pedido_id: int, data: StatusUpdate, db: DbSession, user: Cozinha
):
    estab = user.estabelecimento
    pedido = pedido_crud.alterar_status_pedido(
        db, estab.id, pedido_id, data.status, data.motivo, user.id
    )
    return pedido_crud.pedido_to_dict(pedido, estab)


@router.patch(
    '/{pedido_id}/itens/{item_id}/status', response_model=PedidoResponse
)
def alterar_status_item(
    pedido_id: int,
    item_id: int,
    data: StatusUpdate,
    db: DbSession,
    user: Cozinha,
):
    estab = user.estabelecimento
    pedido = pedido_crud.alterar_status_item(
        db, estab.id, pedido_id, item_id, data.status, data.motivo, user.id
    )
    return pedido_crud.pedido_to_dict(pedido, estab)


@router.patch('/{pedido_id}/previsao', response_model=PedidoResponse)
def atualizar_previsao(
    pedido_id: int, data: PrevisaoUpdate, db: DbSession, user: Cozinha
):
    estab = user.estabelecimento
    pedido = pedido_crud.atualizar_previsao(
        db, estab.id, pedido_id, data, user.id
    )
    return pedido_crud.pedido_to_dict(pedido, estab)
