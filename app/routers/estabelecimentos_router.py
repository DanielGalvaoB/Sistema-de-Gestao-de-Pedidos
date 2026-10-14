from fastapi import APIRouter, HTTPException, status

from app.crud import estabelecimento_crud, mesa_crud
from app.dependencies.auth_dep import Admin, CurrentUser, DbSession
from app.schemas.estabelecimento_schema import (
    EstabelecimentoCreate,
    EstabelecimentoResponse,
    EstabelecimentoUpdate,
)
from app.schemas.mesa_schema import QrCodeResponse

router = APIRouter(prefix='/estabelecimentos', tags=['estabelecimentos'])


@router.post(
    path='/',
    response_model=EstabelecimentoResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(data: EstabelecimentoCreate, db: DbSession):
    """Cadastro publico: cria o estabelecimento e o usuario administrador."""
    return estabelecimento_crud.create_estabelecimento(db, data)


@router.get('/me', response_model=EstabelecimentoResponse)
def get_me(db: DbSession, user: CurrentUser):
    return estabelecimento_crud.get_estabelecimento(
        db, user.id_estabelecimento
    )


@router.get('/me/qrcode', response_model=QrCodeResponse)
def qrcode_geral(db: DbSession, user: CurrentUser):
    est = estabelecimento_crud.get_estabelecimento(db, user.id_estabelecimento)
    return QrCodeResponse(
        url=mesa_crud.url_cardapio(est.slug),
        descricao='Cardapio geral (balcao / retirada)',
    )


@router.get('/{id}', response_model=EstabelecimentoResponse)
def get(id: int, db: DbSession, user: CurrentUser):
    if id != user.id_estabelecimento:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'not found')
    return estabelecimento_crud.get_estabelecimento(db, id)


@router.patch(
    path='/{id}',
    response_model=EstabelecimentoResponse,
    status_code=status.HTTP_200_OK,
)
def update(id: int, data: EstabelecimentoUpdate, db: DbSession, user: Admin):
    if id != user.id_estabelecimento:
        raise HTTPException(status.HTTP_404_NOT_FOUND, 'not found')
    est = estabelecimento_crud.get_estabelecimento(db, id)
    return estabelecimento_crud.update_estabelecimento(db, est, data)
