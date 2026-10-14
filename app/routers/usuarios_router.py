from fastapi import APIRouter, status

from app.crud import usuario_crud
from app.dependencies.auth_dep import Admin, CurrentUser, DbSession
from app.schemas.usuario_schema import (
    SenhaUpdate,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
)

router = APIRouter(prefix='/usuarios', tags=['usuarios'])


@router.get('/', response_model=list[UsuarioResponse])
def list_usuarios(db: DbSession, user: Admin):
    return usuario_crud.list_usuarios(db, user.id_estabelecimento)


@router.post(
    '/', response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED
)
def create_usuario(data: UsuarioCreate, db: DbSession, user: Admin):
    return usuario_crud.create_usuario(db, user.id_estabelecimento, data)


@router.patch('/me/senha', status_code=status.HTTP_204_NO_CONTENT)
def alterar_minha_senha(data: SenhaUpdate, db: DbSession, user: CurrentUser):
    usuario_crud.alterar_senha(db, user, data.senha_atual, data.nova_senha)


@router.patch('/{usuario_id}', response_model=UsuarioResponse)
def update_usuario(
    usuario_id: int, data: UsuarioUpdate, db: DbSession, user: Admin
):
    alvo = usuario_crud.get_usuario(db, user.id_estabelecimento, usuario_id)
    return usuario_crud.update_usuario(db, alvo, data)
