from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import Money, NonEmptyStr, ORMModel


class MenuCreate(BaseModel):
    nome: NonEmptyStr = Field(max_length=120)
    preco: Money
    descricao: str | None = Field(default=None, max_length=500)
    url_imagem: str | None = Field(default=None, max_length=500)
    id_categoria: int
    is_disponivel: bool = True
    tempo_preparo_min: int | None = Field(default=None, ge=1, le=600)


class MenuUpdate(BaseModel):
    nome: NonEmptyStr | None = Field(default=None, max_length=120)
    preco: Money | None = None
    descricao: str | None = Field(default=None, max_length=500)
    url_imagem: str | None = Field(default=None, max_length=500)
    id_categoria: int | None = None
    is_disponivel: bool | None = None
    ativo: bool | None = None
    tempo_preparo_min: int | None = Field(default=None, ge=1, le=600)


class MenuResponse(ORMModel):
    id: int
    nome: str
    preco: Decimal
    descricao: str | None
    url_imagem: str | None
    is_disponivel: bool
    ativo: bool
    tempo_preparo_min: int | None
    id_categoria: int


class HistoricoPrecoResponse(ORMModel):
    preco_anterior: Decimal
    preco_novo: Decimal
    alterado_em: datetime
