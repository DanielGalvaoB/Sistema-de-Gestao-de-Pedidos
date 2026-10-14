from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utcnow
from app.database import Base

Money = Numeric(12, 2)

PERFIS = ('admin', 'atendente', 'cozinha', 'financeiro')
STATUS_PEDIDO = ('recebido', 'em_preparo', 'pronto', 'entregue', 'cancelado')
TIPOS_ATENDIMENTO = ('mesa', 'balcao', 'retirada')
STATUS_SESSAO = ('aberta', 'aguardando_pagamento', 'encerrada', 'cancelada')
STATUS_SESSAO_ABERTA = ('aberta', 'aguardando_pagamento')
METODOS_PAGAMENTO = (
    'dinheiro',
    'cartao_credito',
    'cartao_debito',
    'pix',
    'outro',
)
STATUS_PAGAMENTO = ('confirmado', 'estornado')
TIPOS_MOVIMENTACAO = ('entrada', 'saida')


def _in(col: str, valores: tuple[str, ...]) -> str:
    lista = ', '.join(f"'{v}'" for v in valores)
    return f'{col} IN ({lista})'


class Estabelecimento(Base):
    __tablename__ = 'estabelecimento'

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_loja: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    chave_pix: Mapped[str] = mapped_column(String(140))
    nome_titular: Mapped[str] = mapped_column(String(120))
    cidade: Mapped[str] = mapped_column(String(60), default='SAO PAULO')
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    ativo: Mapped[bool] = mapped_column(default=True)
    # Configuracoes operacionais
    tempo_preparo_padrao_min: Mapped[int] = mapped_column(default=20)
    alerta_atraso_percentual: Mapped[int] = mapped_column(default=80)
    taxa_servico_percentual: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal('0')
    )
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    usuarios: Mapped[list['Usuario']] = relationship(
        back_populates='estabelecimento'
    )
    menus: Mapped[list['Menu']] = relationship(
        back_populates='estabelecimento'
    )
    pedidos: Mapped[list['Pedido']] = relationship(
        back_populates='estabelecimento'
    )


class Usuario(Base):
    __tablename__ = 'usuario'
    __table_args__ = (
        CheckConstraint(_in('perfil', PERFIS), name='ck_perfil'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_estabelecimento: Mapped[int] = mapped_column(
        ForeignKey('estabelecimento.id', ondelete='RESTRICT'), index=True
    )
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    perfil: Mapped[str] = mapped_column(String(20))
    ativo: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    estabelecimento: Mapped[Estabelecimento] = relationship(
        back_populates='usuarios'
    )


class Categoria(Base):
    __tablename__ = 'categoria'
    __table_args__ = (
        UniqueConstraint(
            'id_estabelecimento', 'nome', name='uq_categoria_nome'
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_estabelecimento: Mapped[int] = mapped_column(
        ForeignKey('estabelecimento.id', ondelete='RESTRICT'), index=True
    )
    nome: Mapped[str] = mapped_column(String(80))
    ordem: Mapped[int] = mapped_column(default=0)
    ativo: Mapped[bool] = mapped_column(default=True)

    menus: Mapped[list['Menu']] = relationship(back_populates='categoria')


class Menu(Base):
    """Produto do cardapio."""

    __tablename__ = 'menu'
    __table_args__ = (CheckConstraint('preco >= 0', name='ck_menu_preco'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    preco: Mapped[Decimal] = mapped_column(Money)
    url_imagem: Mapped[str | None] = mapped_column(String(500))
    descricao: Mapped[str | None] = mapped_column(String(500))
    is_disponivel: Mapped[bool] = mapped_column(default=True)
    ativo: Mapped[bool] = mapped_column(default=True)
    tempo_preparo_min: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=utcnow)

    id_categoria: Mapped[int] = mapped_column(
        ForeignKey('categoria.id', ondelete='RESTRICT'), index=True
    )
    id_estabelecimento: Mapped[int] = mapped_column(
        ForeignKey('estabelecimento.id', ondelete='RESTRICT'), index=True
    )

    categoria: Mapped[Categoria] = relationship(back_populates='menus')
    estabelecimento: Mapped[Estabelecimento] = relationship(
        back_populates='menus'
    )
    historico_precos: Mapped[list['HistoricoPreco']] = relationship(
        back_populates='menu',
        order_by='HistoricoPreco.id',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )


class HistoricoPreco(Base):
    __tablename__ = 'historico_preco'

    id: Mapped[int] = mapped_column(primary_key=True)
    id_menu: Mapped[int] = mapped_column(
        ForeignKey('menu.id', ondelete='CASCADE'), index=True
    )
    preco_anterior: Mapped[Decimal] = mapped_column(Money)
    preco_novo: Mapped[Decimal] = mapped_column(Money)
    id_usuario: Mapped[int | None] = mapped_column(
        ForeignKey('usuario.id', ondelete='SET NULL')
    )
    alterado_em: Mapped[datetime] = mapped_column(default=utcnow)

    menu: Mapped[Menu] = relationship(back_populates='historico_precos')


class Mesa(Base):
    __tablename__ = 'mesa'
    __table_args__ = (
        UniqueConstraint(
            'id_estabelecimento', 'numero', name='uq_mesa_numero'
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_estabelecimento: Mapped[int] = mapped_column(
        ForeignKey('estabelecimento.id', ondelete='RESTRICT'), index=True
    )
    numero: Mapped[str] = mapped_column(String(20))
    capacidade: Mapped[int | None]
    ativo: Mapped[bool] = mapped_column(default=True)
    # Token publico usado no QR Code (nao expoe o id sequencial)
    token: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    sessoes: Mapped[list['SessaoAtendimento']] = relationship(
        back_populates='mesa'
    )


class SessaoAtendimento(Base):
    """Conta: agrupa os pedidos de uma mesa (ou de um cliente no balcao)."""

    __tablename__ = 'sessao_atendimento'
    __table_args__ = (
        CheckConstraint(_in('tipo', TIPOS_ATENDIMENTO), name='ck_sessao_tipo'),
        CheckConstraint(_in('status', STATUS_SESSAO), name='ck_sessao_status'),
        CheckConstraint('desconto >= 0', name='ck_sessao_desconto'),
        CheckConstraint('acrescimo >= 0', name='ck_sessao_acrescimo'),
        # Uma mesa so pode ter uma conta aberta por vez
        Index(
            'uq_sessao_mesa_aberta',
            'id_mesa',
            unique=True,
            sqlite_where=text("status IN ('aberta', 'aguardando_pagamento')"),
            postgresql_where=text(
                "status IN ('aberta', 'aguardando_pagamento')"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_estabelecimento: Mapped[int] = mapped_column(
        ForeignKey('estabelecimento.id', ondelete='RESTRICT'), index=True
    )
    id_mesa: Mapped[int | None] = mapped_column(
        ForeignKey('mesa.id', ondelete='RESTRICT'), index=True
    )
    tipo: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default='aberta')
    cliente_nome: Mapped[str | None] = mapped_column(String(80))
    desconto: Mapped[Decimal] = mapped_column(Money, default=Decimal('0'))
    motivo_desconto: Mapped[str | None] = mapped_column(String(200))
    acrescimo: Mapped[Decimal] = mapped_column(Money, default=Decimal('0'))
    motivo_acrescimo: Mapped[str | None] = mapped_column(String(200))
    aberta_em: Mapped[datetime] = mapped_column(default=utcnow, index=True)
    encerrada_em: Mapped[datetime | None]

    mesa: Mapped[Mesa | None] = relationship(back_populates='sessoes')
    pedidos: Mapped[list['Pedido']] = relationship(
        back_populates='sessao', order_by='Pedido.id'
    )
    pagamentos: Mapped[list['Pagamento']] = relationship(
        back_populates='sessao', order_by='Pagamento.id'
    )


class Pedido(Base):
    __tablename__ = 'pedido'
    __table_args__ = (
        CheckConstraint(_in('status', STATUS_PEDIDO), name='ck_pedido_status'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_estabelecimento: Mapped[int] = mapped_column(
        ForeignKey('estabelecimento.id', ondelete='RESTRICT'), index=True
    )
    id_sessao: Mapped[int] = mapped_column(
        ForeignKey('sessao_atendimento.id', ondelete='RESTRICT'), index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default='recebido', index=True
    )
    observacao: Mapped[str | None] = mapped_column(String(500))
    # Token do link publico de acompanhamento
    codigo_acompanhamento: Mapped[str] = mapped_column(
        String(40), unique=True, index=True
    )
    origem: Mapped[str] = mapped_column(String(20), default='cliente')
    previsao_pronto: Mapped[datetime | None]
    motivo_atraso: Mapped[str | None] = mapped_column(String(300))
    motivo_cancelamento: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)
    iniciado_em: Mapped[datetime | None]
    pronto_em: Mapped[datetime | None]
    entregue_em: Mapped[datetime | None]
    cancelado_em: Mapped[datetime | None]

    estabelecimento: Mapped[Estabelecimento] = relationship(
        back_populates='pedidos'
    )
    sessao: Mapped[SessaoAtendimento] = relationship(back_populates='pedidos')
    itens: Mapped[list['ItemPedido']] = relationship(
        back_populates='pedido',
        cascade='all, delete-orphan',
        order_by='ItemPedido.id',
    )
    historico: Mapped[list['HistoricoStatusPedido']] = relationship(
        back_populates='pedido', order_by='HistoricoStatusPedido.id'
    )
    pagamentos: Mapped[list['Pagamento']] = relationship(
        order_by='Pagamento.id', viewonly=True
    )


class ItemPedido(Base):
    __tablename__ = 'item_pedido'
    __table_args__ = (
        CheckConstraint('quantidade > 0', name='ck_item_quantidade'),
        CheckConstraint('preco_unitario >= 0', name='ck_item_preco'),
        CheckConstraint(_in('status', STATUS_PEDIDO), name='ck_item_status'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_pedido: Mapped[int] = mapped_column(
        ForeignKey('pedido.id', ondelete='CASCADE'), index=True
    )
    id_menu: Mapped[int] = mapped_column(
        ForeignKey('menu.id', ondelete='RESTRICT'), index=True
    )
    # Snapshot do produto no momento da compra
    nome_produto: Mapped[str] = mapped_column(String(120))
    preco_unitario: Mapped[Decimal] = mapped_column(Money)
    quantidade: Mapped[int]
    subtotal: Mapped[Decimal] = mapped_column(Money)
    observacao: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), default='recebido')
    iniciado_em: Mapped[datetime | None]
    pronto_em: Mapped[datetime | None]

    pedido: Mapped[Pedido] = relationship(back_populates='itens')
    menu: Mapped[Menu] = relationship()


class HistoricoStatusPedido(Base):
    __tablename__ = 'historico_status_pedido'

    id: Mapped[int] = mapped_column(primary_key=True)
    id_pedido: Mapped[int] = mapped_column(
        ForeignKey('pedido.id', ondelete='CASCADE'), index=True
    )
    id_item: Mapped[int | None] = mapped_column(
        ForeignKey('item_pedido.id', ondelete='CASCADE')
    )
    status_anterior: Mapped[str | None] = mapped_column(String(20))
    status_novo: Mapped[str] = mapped_column(String(20))
    motivo: Mapped[str | None] = mapped_column(String(300))
    id_usuario: Mapped[int | None] = mapped_column(
        ForeignKey('usuario.id', ondelete='SET NULL')
    )
    criado_em: Mapped[datetime] = mapped_column(default=utcnow)

    pedido: Mapped[Pedido] = relationship(back_populates='historico')


class Pagamento(Base):
    __tablename__ = 'pagamento'
    __table_args__ = (
        CheckConstraint('valor > 0', name='ck_pagamento_valor'),
        CheckConstraint(
            _in('metodo', METODOS_PAGAMENTO), name='ck_pagamento_metodo'
        ),
        CheckConstraint(
            _in('status', STATUS_PAGAMENTO), name='ck_pagamento_status'
        ),
        UniqueConstraint(
            'id_estabelecimento',
            'chave_idempotencia',
            name='uq_pagamento_idempotencia',
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_estabelecimento: Mapped[int] = mapped_column(
        ForeignKey('estabelecimento.id', ondelete='RESTRICT'), index=True
    )
    id_sessao: Mapped[int] = mapped_column(
        ForeignKey('sessao_atendimento.id', ondelete='RESTRICT'), index=True
    )
    # Pedido quitado por este pagamento (opcional: pagamentos da conta
    # inteira nao apontam para um pedido especifico)
    id_pedido: Mapped[int | None] = mapped_column(
        ForeignKey('pedido.id', ondelete='RESTRICT'), index=True
    )
    valor: Mapped[Decimal] = mapped_column(Money)
    metodo: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default='confirmado')
    # 'manual' = registrado por um funcionario; 'provedor' = confirmado
    # por notificacao autenticada de um provedor de pagamentos
    origem: Mapped[str] = mapped_column(String(20), default='manual')
    chave_idempotencia: Mapped[str] = mapped_column(String(80))
    observacao: Mapped[str | None] = mapped_column(String(300))
    id_usuario: Mapped[int | None] = mapped_column(
        ForeignKey('usuario.id', ondelete='SET NULL')
    )
    data_hora: Mapped[datetime] = mapped_column(default=utcnow, index=True)
    estornado_em: Mapped[datetime | None]
    motivo_estorno: Mapped[str | None] = mapped_column(String(300))

    sessao: Mapped[SessaoAtendimento] = relationship(
        back_populates='pagamentos'
    )


class CobrancaPix(Base):
    __tablename__ = 'cobranca_pix'

    id: Mapped[int] = mapped_column(primary_key=True)
    id_estabelecimento: Mapped[int] = mapped_column(
        ForeignKey('estabelecimento.id', ondelete='RESTRICT'), index=True
    )
    id_sessao: Mapped[int] = mapped_column(
        ForeignKey('sessao_atendimento.id', ondelete='RESTRICT'), index=True
    )
    txid: Mapped[str] = mapped_column(String(35), unique=True)
    valor: Mapped[Decimal] = mapped_column(Money)
    copia_e_cola: Mapped[str] = mapped_column(String(512))
    # 'estatico' = BR Code gerado localmente, sem confirmacao automatica
    provedor: Mapped[str] = mapped_column(String(30), default='estatico')
    status: Mapped[str] = mapped_column(String(20), default='pendente')
    id_pagamento: Mapped[int | None] = mapped_column(
        ForeignKey('pagamento.id', ondelete='SET NULL')
    )
    criada_em: Mapped[datetime] = mapped_column(default=utcnow)


class CategoriaFinanceira(Base):
    __tablename__ = 'categoria_financeira'
    __table_args__ = (
        UniqueConstraint(
            'id_estabelecimento', 'nome', 'tipo', name='uq_cat_fin_nome'
        ),
        CheckConstraint(
            _in('tipo', TIPOS_MOVIMENTACAO), name='ck_cat_fin_tipo'
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_estabelecimento: Mapped[int] = mapped_column(
        ForeignKey('estabelecimento.id', ondelete='RESTRICT'), index=True
    )
    nome: Mapped[str] = mapped_column(String(80))
    tipo: Mapped[str] = mapped_column(String(10))
    ativo: Mapped[bool] = mapped_column(default=True)
    # Categorias de sistema (ex.: "Vendas") nao podem ser editadas
    sistema: Mapped[bool] = mapped_column(default=False)


class MovimentacaoFinanceira(Base):
    __tablename__ = 'movimentacao_financeira'
    __table_args__ = (
        CheckConstraint('valor > 0', name='ck_mov_valor'),
        CheckConstraint(_in('tipo', TIPOS_MOVIMENTACAO), name='ck_mov_tipo'),
        CheckConstraint(
            "status IN ('ativa', 'cancelada')", name='ck_mov_status'
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_estabelecimento: Mapped[int] = mapped_column(
        ForeignKey('estabelecimento.id', ondelete='RESTRICT'), index=True
    )
    tipo: Mapped[str] = mapped_column(String(10))
    descricao: Mapped[str] = mapped_column(String(200))
    id_categoria: Mapped[int] = mapped_column(
        ForeignKey('categoria_financeira.id', ondelete='RESTRICT')
    )
    valor: Mapped[Decimal] = mapped_column(Money)
    data_hora: Mapped[datetime] = mapped_column(default=utcnow, index=True)
    metodo_pagamento: Mapped[str | None] = mapped_column(String(20))
    observacao: Mapped[str | None] = mapped_column(String(500))
    id_usuario: Mapped[int | None] = mapped_column(
        ForeignKey('usuario.id', ondelete='SET NULL')
    )
    # Um pagamento gera no maximo uma entrada (evita receita duplicada)
    id_pagamento: Mapped[int | None] = mapped_column(
        ForeignKey('pagamento.id', ondelete='RESTRICT'), unique=True
    )
    status: Mapped[str] = mapped_column(String(20), default='ativa')
    cancelado_em: Mapped[datetime | None]
    motivo_cancelamento: Mapped[str | None] = mapped_column(String(300))
    id_usuario_cancelamento: Mapped[int | None] = mapped_column(
        ForeignKey('usuario.id', ondelete='SET NULL')
    )
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    categoria: Mapped[CategoriaFinanceira] = relationship()
