from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import NonEmptyStr, ORMModel


class EstabelecimentoCreate(BaseModel):
    """Cadastro de um novo estabelecimento e do seu usuario administrador."""

    nome_loja: NonEmptyStr = Field(max_length=120)
    chave_pix: NonEmptyStr = Field(max_length=140)
    nome_titular: NonEmptyStr = Field(max_length=120)
    cidade: NonEmptyStr = Field(default='SAO PAULO', max_length=60)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    nome_admin: NonEmptyStr | None = Field(default=None, max_length=120)


class EstabelecimentoUpdate(BaseModel):
    nome_loja: NonEmptyStr | None = Field(default=None, max_length=120)
    chave_pix: NonEmptyStr | None = Field(default=None, max_length=140)
    nome_titular: NonEmptyStr | None = Field(default=None, max_length=120)
    cidade: NonEmptyStr | None = Field(default=None, max_length=60)
    email: EmailStr | None = None
    taxa_servico_percentual: Decimal | None = Field(
        default=None, ge=0, le=30, decimal_places=2
    )


class EstabelecimentoResponse(ORMModel):
    id: int
    nome_loja: str
    slug: str
    email: str
    nome_titular: str
    chave_pix: str
    cidade: str
    taxa_servico_percentual: Decimal


class EstabelecimentoPublico(ORMModel):
    """Dados expostos no cardapio publico (sem email nem chave PIX)."""

    nome_loja: str
    slug: str
