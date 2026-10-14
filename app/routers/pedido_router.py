from datetime import date

from fastapi import APIRouter, Query, Response, status

from app.core.errors import BusinessRuleError
from app.core.utils import periodo_utc
from app.crud import mesa_crud, pedido_crud
from app.dependencies.auth_dep import Atendimento, Caixa, Cozinha, DbSession
from app.schemas.pedido_schema import (
    PagamentoPedidoCreate,
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


@router.post(
    '/{pedido_id}/pagamentos',
    response_model=PedidoResponse,
    status_code=status.HTTP_201_CREATED,
)
def confirmar_pagamento(
    pedido_id: int,
    data: PagamentoPedidoCreate,
    db: DbSession,
    user: Caixa,
    response: Response,
):
    """Confirma (manualmente) o pagamento de um pedido pronto ou entregue.

    Informe a forma de pagamento; sem `valor`, quita o saldo do pedido.
    Reenvios com a mesma `chave_idempotencia` devolvem HTTP 200.
    """
    estab = user.estabelecimento
    pedido, criado = pedido_crud.pagar_pedido(
        db, estab, pedido_id, data, user.id
    )
    if not criado:
        response.status_code = status.HTTP_200_OK
    return pedido_crud.pedido_to_dict(pedido, estab)
