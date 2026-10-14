from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import NonEmptyStr, ORMModel


class MesaCreate(BaseModel):
    numero: NonEmptyStr = Field(max_length=20)
    capacidade: int | None = Field(default=None, ge=1, le=100)


class MesaUpdate(BaseModel):
    numero: NonEmptyStr | None = Field(default=None, max_length=20)
    capacidade: int | None = Field(default=None, ge=1, le=100)
    ativo: bool | None = None


class MesaResponse(ORMModel):
    id: int
    numero: str
    capacidade: int | None
    ativo: bool
    token: str


class MesaPainel(MesaResponse):
    """Mesa com a situacao atual (livre/ocupada/aguardando_pagamento)."""

    situacao: str
    id_sessao: int | None = None
    aberta_em: datetime | None = None
    total_consumido: Decimal = Decimal('0.00')


class QrCodeResponse(BaseModel):
    url: str
    descricao: str
