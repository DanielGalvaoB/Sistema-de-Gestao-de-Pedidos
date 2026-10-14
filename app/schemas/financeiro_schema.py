from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import NonEmptyStr, ORMModel, PositiveMoney

# O sistema controla apenas o que entra (sem despesas do estabelecimento)
TipoMov = Literal['entrada']


class CategoriaFinanceiraCreate(BaseModel):
    nome: NonEmptyStr = Field(max_length=80)
    tipo: TipoMov = 'entrada'


class CategoriaFinanceiraUpdate(BaseModel):
    nome: NonEmptyStr | None = Field(default=None, max_length=80)
    ativo: bool | None = None


class CategoriaFinanceiraResponse(ORMModel):
    id: int
    nome: str
    tipo: str
    ativo: bool
    sistema: bool


class MovimentacaoCreate(BaseModel):
    tipo: TipoMov = 'entrada'
    descricao: NonEmptyStr = Field(max_length=200)
    id_categoria: int
    valor: PositiveMoney
    data_hora: datetime | None = None
    metodo_pagamento: str | None = Field(default=None, max_length=20)
    observacao: str | None = Field(default=None, max_length=500)


class MovimentacaoUpdate(BaseModel):
    descricao: NonEmptyStr | None = Field(default=None, max_length=200)
    id_categoria: int | None = None
    valor: PositiveMoney | None = None
    data_hora: datetime | None = None
    metodo_pagamento: str | None = Field(default=None, max_length=20)
    observacao: str | None = Field(default=None, max_length=500)


class CancelamentoRequest(BaseModel):
    motivo: str = Field(min_length=3, max_length=300)


class MovimentacaoResponse(ORMModel):
    id: int
    tipo: str
    descricao: str
    id_categoria: int
    categoria_nome: str
    valor: Decimal
    data_hora: datetime
    metodo_pagamento: str | None
    observacao: str | None
    id_pagamento: int | None
    status: str
    cancelado_em: datetime | None
    motivo_cancelamento: str | None
    automatica: bool


class FiltroPeriodo(BaseModel):
    inicio: date
    fim: date


class SerieDia(BaseModel):
    dia: date
    vendas: Decimal
    recebido: Decimal


class ValorRotulo(BaseModel):
    rotulo: str
    valor: Decimal
    quantidade: int = 0


class RelatorioResumo(BaseModel):
    inicio: date
    fim: date
    criterios: dict[str, str]
    total_vendas: Decimal
    total_recebido: Decimal
    outras_entradas: Decimal
    total_entradas: Decimal
    pendente_recebimento: Decimal
    quantidade_pedidos: int
    ticket_medio: Decimal
    produtos_mais_vendidos: list[ValorRotulo]
    vendas_por_dia: list[SerieDia]
    recebido_por_metodo: list[ValorRotulo]
