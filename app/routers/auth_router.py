from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import create_access_token
from app.crud import usuario_crud
from app.dependencies.auth_dep import CurrentUser, DbSession
from app.schemas.usuario_schema import LoginRequest, Me, Token

router = APIRouter(prefix='/auth', tags=['auth'])


def _login(db, email: str, password: str) -> Token:
    user = usuario_crud.autenticar(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Email ou senha incorretos',
        )
    return Token(access_token=create_access_token(user.id))


@router.post('/token', response_model=Token)
def token(
    db: DbSession, form: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """Login no formato OAuth2 (usado pelo botao Authorize do /docs)."""
    return _login(db, form.username, form.password)


@router.post('/login', response_model=Token)
def login(db: DbSession, data: LoginRequest):
    return _login(db, data.email, data.password)


@router.get('/me', response_model=Me)
def me(user: CurrentUser):
    return Me(
        id=user.id,
        nome=user.nome,
        email=user.email,
        perfil=user.perfil,
        ativo=user.ativo,
        id_estabelecimento=user.id_estabelecimento,
        nome_loja=user.estabelecimento.nome_loja,
        slug=user.estabelecimento.slug,
    )
