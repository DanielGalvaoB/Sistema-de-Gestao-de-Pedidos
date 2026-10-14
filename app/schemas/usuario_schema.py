from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import NonEmptyStr, ORMModel

Perfil = Literal['admin', 'atendente', 'cozinha', 'financeiro']


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class UsuarioCreate(BaseModel):
    nome: NonEmptyStr = Field(max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    perfil: Perfil


class UsuarioUpdate(BaseModel):
    nome: NonEmptyStr | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    perfil: Perfil | None = None
    ativo: bool | None = None


class SenhaUpdate(BaseModel):
    senha_atual: str
    nova_senha: str = Field(min_length=8, max_length=72)


class UsuarioResponse(ORMModel):
    id: int
    nome: str
    email: str
    perfil: str
    ativo: bool
    id_estabelecimento: int


class Me(UsuarioResponse):
    nome_loja: str
    slug: str
