from fastapi import APIRouter, HTTPException, Query, Response, status

from app.crud import conta_crud, mesa_crud, pedido_crud
from app.dependencies.auth_dep import Atendimento, Caixa, DbSession
from app.schemas.conta_schema import (
    AjusteConta,
    CobrancaPixCreate,
    CobrancaPixResponse,
    EstornoRequest,
    PagamentoCreate,
    PagamentoResponse,
    SessaoCreate,
    SessaoDetalhe,
)

router = APIRouter(prefix='/contas', tags=['contas e pagamentos'])


def _detalhe(sessao, estab):
    dados = conta_crud.sessao_to_dict(sessao)
    dados['pedidos'] = [
        pedido_crud.pedido_to_dict(p, estab) for p in sessao.pedidos
    ]
    dados['pagamentos'] = sessao.pagamentos
    return dados


@router.get('/', response_model=list[SessaoDetalhe])
def list_contas(
    db: DbSession,
    user: Caixa,
    status_: list[str] | None = Query(default=None, alias='status'),
    com_pedidos: bool = False,
):
    """Lista contas. Com `com_pedidos=true` traz os pedidos e pagamentos."""
    sessoes = conta_crud.list_sessoes(db, user.id_estabelecimento, status_)
    if com_pedidos:
        return [_detalhe(s, user.estabelecimento) for s in sessoes]
    return [
        {**conta_crud.sessao_to_dict(s), 'pedidos': [], 'pagamentos': []}
        for s in sessoes
    ]


@router.post(
    '/', response_model=SessaoDetalhe, status_code=status.HTTP_201_CREATED
)
def abrir_conta(data: SessaoCreate, db: DbSession, user: Atendimento):
    mesa = None
    if data.id_mesa is not None:
        mesa = mesa_crud.get_mesa(db, user.id_estabelecimento, data.id_mesa)
        if mesa_crud.sessao_aberta_da_mesa(db, mesa.id):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                'Esta mesa ja possui uma conta aberta',
            )
    sessao = conta_crud.abrir_sessao(
        db, user.id_estabelecimento, mesa, data.tipo, data.cliente_nome
    )
    db.commit()
    sessao = conta_crud.get_sessao(db, user.id_estabelecimento, sessao.id)
    return _detalhe(sessao, user.estabelecimento)


@router.get('/{sessao_id}', response_model=SessaoDetalhe)
def get_conta(sessao_id: int, db: DbSession, user: Caixa):
    sessao = conta_crud.get_sessao(db, user.id_estabelecimento, sessao_id)
    return _detalhe(sessao, user.estabelecimento)


@router.patch('/{sessao_id}/ajustes', response_model=SessaoDetalhe)
def ajustar(sessao_id: int, data: AjusteConta, db: DbSession, user: Caixa):
    if data.desconto and user.perfil not in {'admin', 'financeiro'}:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            'Descontos precisam ser autorizados por admin ou financeiro',
        )
    sessao = conta_crud.ajustar_conta(
        db, user.estabelecimento, sessao_id, data
    )
    return _detalhe(sessao, user.estabelecimento)


@router.post('/{sessao_id}/solicitar-fechamento', response_model=SessaoDetalhe)
def solicitar_fechamento(sessao_id: int, db: DbSession, user: Caixa):
    sessao = conta_crud.solicitar_fechamento(
        db, user.id_estabelecimento, sessao_id
    )
    return _detalhe(sessao, user.estabelecimento)


@router.post('/{sessao_id}/encerrar', response_model=SessaoDetalhe)
def encerrar(sessao_id: int, db: DbSession, user: Caixa):
    """Encerra a conta. Recusado se houver saldo ou pedidos em andamento."""
    sessao = conta_crud.encerrar_sessao(db, user.id_estabelecimento, sessao_id)
    return _detalhe(sessao, user.estabelecimento)


@router.post('/{sessao_id}/cancelar', response_model=SessaoDetalhe)
def cancelar(sessao_id: int, db: DbSession, user: Caixa):
    sessao = conta_crud.cancelar_sessao(db, user.id_estabelecimento, sessao_id)
    return _detalhe(sessao, user.estabelecimento)


@router.post(
    '/{sessao_id}/pagamentos',
    response_model=PagamentoResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_pagamento(
    sessao_id: int,
    data: PagamentoCreate,
    db: DbSession,
    user: Caixa,
    response: Response,
):
    """Registro MANUAL de pagamento, feito por um funcionario.

    Reenvios com a mesma `chave_idempotencia` devolvem o pagamento original
    (HTTP 200) em vez de criar outro.
    """
    pagamento, criado = conta_crud.registrar_pagamento(
        db, user.id_estabelecimento, sessao_id, data, user.id
    )
    if not criado:
        response.status_code = status.HTTP_200_OK
    return pagamento


@router.post(
    '/pagamentos/{pagamento_id}/estornar', response_model=PagamentoResponse
)
def estornar(
    pagamento_id: int, data: EstornoRequest, db: DbSession, user: Caixa
):
    return conta_crud.estornar_pagamento(
        db, user.id_estabelecimento, pagamento_id, data.motivo, user.id
    )


@router.post(
    '/{sessao_id}/pix',
    response_model=CobrancaPixResponse,
    status_code=status.HTTP_201_CREATED,
)
def gerar_pix(
    sessao_id: int, data: CobrancaPixCreate, db: DbSession, user: Caixa
):
    return conta_crud.gerar_cobranca_pix(
        db, user.estabelecimento, sessao_id, data.valor
    )


@router.get('/{sessao_id}/pix', response_model=list[CobrancaPixResponse])
def listar_pix(sessao_id: int, db: DbSession, user: Caixa):
    return conta_crud.list_cobrancas(db, user.id_estabelecimento, sessao_id)
