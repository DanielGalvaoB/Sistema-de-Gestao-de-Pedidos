from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel

StatusPedido = Literal[
    'recebido', 'em_preparo', 'pronto', 'entregue', 'cancelado'
]
TipoAtendimento = Literal['mesa', 'balcao', 'retirada']


class ItemPedidoCreate(BaseModel):
    id_menu: int
    quantidade: int = Field(gt=0, le=100)
    observacao: str | None = Field(default=None, max_length=300)


class PedidoCreate(BaseModel):
    """Pedido registrado pela equipe.

    Informe `id_sessao` (conta ja aberta), `id_mesa` (abre ou reaproveita a
    conta da mesa) ou nenhum dos dois para balcao/retirada.
    """

    id_sessao: int | None = None
    id_mesa: int | None = None
    tipo: TipoAtendimento | None = None
    cliente_nome: str | None = Field(default=None, max_length=80)
    observacao: str | None = Field(default=None, max_length=500)
    itens: list[ItemPedidoCreate] = Field(min_length=1, max_length=50)


class PedidoPublicoCreate(BaseModel):
    """Pedido enviado pelo cliente a partir do cardapio publico."""

    mesa_token: str | None = Field(default=None, max_length=40)
    # Codigo de acompanhamento de um pedido anterior: o novo pedido entra
    # na mesma conta (mesma pessoa/mesa) enquanto ela estiver aberta.
    codigo_origem: str | None = Field(default=None, max_length=40)
    tipo: TipoAtendimento = 'balcao'
    cliente_nome: str | None = Field(default=None, max_length=80)
    observacao: str | None = Field(default=None, max_length=500)
    itens: list[ItemPedidoCreate] = Field(min_length=1, max_length=50)


class StatusUpdate(BaseModel):
    status: StatusPedido
    motivo: str | None = Field(default=None, max_length=300)


class PagamentoPedidoCreate(BaseModel):
    metodo: Literal[
        'dinheiro', 'cartao_credito', 'cartao_debito', 'pix', 'outro'
    ]
    # Opcional: sem valor, quita o saldo do pedido
    valor: Decimal | None = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )
    chave_idempotencia: str = Field(min_length=8, max_length=80)
    observacao: str | None = Field(default=None, max_length=300)


class PrevisaoUpdate(BaseModel):
    previsao_pronto: datetime | None = None
    minutos_adicionais: int | None = Field(default=None, ge=1, le=600)
    motivo_atraso: str | None = Field(default=None, max_length=300)


class ItemPedidoResponse(ORMModel):
    id: int
    id_menu: int
    nome_produto: str
    preco_unitario: Decimal
    quantidade: int
    subtotal: Decimal
    observacao: str | None
    status: str
    iniciado_em: datetime | None
    pronto_em: datetime | None
    previsao_pronto: datetime | None = None
    atrasado: bool = False


class HistoricoResponse(ORMModel):
    id_item: int | None
    status_anterior: str | None
    status_novo: str
    motivo: str | None
    criado_em: datetime


class PedidoResponse(ORMModel):
    id: int
    id_sessao: int
    status: str
    observacao: str | None
    origem: str
    codigo_acompanhamento: str
    created_at: datetime
    iniciado_em: datetime | None
    pronto_em: datetime | None
    entregue_em: datetime | None
    cancelado_em: datetime | None
    previsao_pronto: datetime | None
    motivo_atraso: str | None
    motivo_cancelamento: str | None
    total: Decimal
    total_pago: Decimal
    saldo: Decimal
    pago: bool
    tipo_atendimento: str
    mesa_numero: str | None
    cliente_nome: str | None
    atrasado: bool
    minutos_atraso: int
    alerta_prazo: bool
    itens: list[ItemPedidoResponse]


class PedidoDetalhe(PedidoResponse):
    historico: list[HistoricoResponse]


class ItemAcompanhamento(BaseModel):
    nome_produto: str
    quantidade: int
    status: str


class PedidoAcompanhamento(BaseModel):
    """Visao publica do pedido: sem dados pessoais nem dados de outros."""

    numero: int
    nome_loja: str
    slug: str
    status: str
    tipo_atendimento: str
    mesa_numero: str | None
    created_at: datetime
    iniciado_em: datetime | None
    pronto_em: datetime | None
    entregue_em: datetime | None
    previsao_pronto: datetime | None
    atrasado: bool
    motivo_atraso: str | None
    total: Decimal
    itens: list[ItemAcompanhamento]


class ContaAcompanhamento(BaseModel):
    """Pedidos da mesma conta, vistos pelo cliente (sem dados pessoais)."""

    nome_loja: str
    slug: str
    tipo_atendimento: str
    mesa_numero: str | None
    conta_aberta: bool
    total: Decimal
    pedidos: list[PedidoAcompanhamento]
