from fastapi import APIRouter, status

from app.crud import conta_crud, mesa_crud
from app.dependencies.auth_dep import Admin, Atendimento, DbSession
from app.schemas.conta_schema import SessaoResponse
from app.schemas.mesa_schema import (
    MesaCreate,
    MesaPainel,
    MesaResponse,
    MesaUpdate,
    QrCodeResponse,
)

router = APIRouter(prefix='/mesas', tags=['mesas'])


@router.get('/', response_model=list[MesaPainel])
def painel_mesas(
    db: DbSession, user: Atendimento, incluir_inativas: bool = False
):
    """Mesas com a situacao atual: livre, ocupada ou aguardando_pagamento."""
    saida = []
    for mesa in mesa_crud.list_mesas(
        db, user.id_estabelecimento, incluir_inativas
    ):
        dados = MesaResponse.model_validate(mesa).model_dump()
        sessao = mesa_crud.sessao_aberta_da_mesa(db, mesa.id)
        if sessao:
            sessao = conta_crud.get_sessao(
                db, user.id_estabelecimento, sessao.id
            )
            dados.update(
                situacao='ocupada'
                if sessao.status == 'aberta'
                else 'aguardando_pagamento',
                id_sessao=sessao.id,
                aberta_em=sessao.aberta_em,
                total_consumido=conta_crud.resumo(sessao)['total'],
            )
        else:
            dados['situacao'] = 'livre'
        saida.append(dados)
    return saida


@router.post(
    '/', response_model=MesaResponse, status_code=status.HTTP_201_CREATED
)
def create_mesa(data: MesaCreate, db: DbSession, user: Admin):
    return mesa_crud.create_mesa(db, user.id_estabelecimento, data)


@router.patch('/{mesa_id}', response_model=MesaResponse)
def update_mesa(mesa_id: int, data: MesaUpdate, db: DbSession, user: Admin):
    mesa = mesa_crud.get_mesa(db, user.id_estabelecimento, mesa_id)
    return mesa_crud.update_mesa(db, mesa, data)


@router.get('/{mesa_id}/qrcode', response_model=QrCodeResponse)
def qrcode_mesa(mesa_id: int, db: DbSession, user: Atendimento):
    mesa = mesa_crud.get_mesa(db, user.id_estabelecimento, mesa_id)
    return QrCodeResponse(
        url=mesa_crud.url_cardapio(user.estabelecimento.slug, mesa.token),
        descricao=f'Mesa {mesa.numero}',
    )


@router.post('/{mesa_id}/regenerar-token', response_model=MesaResponse)
def regenerar_token(mesa_id: int, db: DbSession, user: Admin):
    """Invalida o QR Code impresso anterior da mesa."""
    mesa = mesa_crud.get_mesa(db, user.id_estabelecimento, mesa_id)
    return mesa_crud.regenerar_token(db, mesa)


@router.get('/{mesa_id}/historico', response_model=list[SessaoResponse])
def historico_mesa(mesa_id: int, db: DbSession, user: Atendimento):
    """Contas anteriores da mesa (mais recentes primeiro)."""
    mesa = mesa_crud.get_mesa(db, user.id_estabelecimento, mesa_id)
    sessoes = sorted(mesa.sessoes, key=lambda s: s.aberta_em, reverse=True)
    return [
        conta_crud.sessao_to_dict(
            conta_crud.get_sessao(db, user.id_estabelecimento, s.id)
        )
        for s in sessoes[:50]
    ]
