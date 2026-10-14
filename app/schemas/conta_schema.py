from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import Money, ORMModel, PositiveMoney
from app.schemas.pedido_schema import PedidoResponse, TipoAtendimento

MetodoPagamento = Literal[
    'dinheiro', 'cartao_credito', 'cartao_debito', 'pix', 'outro'
]


class SessaoCreate(BaseModel):
    id_mesa: int | None = None
    tipo: TipoAtendimento = 'mesa'
    cliente_nome: str | None = Field(default=None, max_length=80)


class AjusteConta(BaseModel):
    desconto: Money | None = None
    motivo_desconto: str | None = Field(default=None, max_length=200)
    acrescimo: Money | None = None
    motivo_acrescimo: str | None = Field(default=None, max_length=200)
    aplicar_taxa_servico: bool = False


class PagamentoCreate(BaseModel):
    valor: PositiveMoney
    metodo: MetodoPagamento
    # Gerada pelo frontend a cada tentativa; reenvios com a mesma chave
    # devolvem o pagamento ja registrado em vez de duplicar.
    chave_idempotencia: str = Field(min_length=8, max_length=80)
    observacao: str | None = Field(default=None, max_length=300)


class EstornoRequest(BaseModel):
    motivo: str = Field(min_length=3, max_length=300)


class PagamentoResponse(ORMModel):
    id: int
    id_sessao: int
    valor: Decimal
    metodo: str
    status: str
    origem: str
    observacao: str | None
    data_hora: datetime
    estornado_em: datetime | None
    motivo_estorno: str | None


class ResumoConta(BaseModel):
    subtotal: Decimal
    desconto: Decimal
    acrescimo: Decimal
    total: Decimal
    total_pago: Decimal
    saldo: Decimal


class SessaoResponse(ORMModel):
    id: int
    tipo: str
    status: str
    id_mesa: int | None
    mesa_numero: str | None
    cliente_nome: str | None
    aberta_em: datetime
    encerrada_em: datetime | None
    motivo_desconto: str | None
    motivo_acrescimo: str | None
    resumo: ResumoConta


class SessaoDetalhe(SessaoResponse):
    pedidos: list[PedidoResponse]
    pagamentos: list[PagamentoResponse]


class CobrancaPixCreate(BaseModel):
    valor: PositiveMoney | None = None


class CobrancaPixResponse(ORMModel):
    id: int
    txid: str
    valor: Decimal
    copia_e_cola: str
    provedor: str
    status: str
    criada_em: datetime
    confirmacao_automatica: bool = False
    aviso: str = (
        'Cobranca PIX estatica: nao ha provedor integrado, entao o '
        'recebimento NAO e confirmado automaticamente. Confira no extrato '
        'bancario e registre o pagamento manualmente.'
    )
