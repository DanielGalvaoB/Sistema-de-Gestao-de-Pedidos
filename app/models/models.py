from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Categoria(Base):
    __tablename__ = 'categoria'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)

    # Relacionamento: Uma categoria tem muitos itens de menu
    menus = relationship('Menu', back_populates='categoria')


class Estabelecimento(Base):
    __tablename__ = 'estabelecimento'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_loja = Column(String, nullable=False)
    chave_pix = Column(String, nullable=False)
    nome_titular = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    menus = relationship('Menu', back_populates='estabelecimento')
    pedidos = relationship('Pedido', back_populates='estabelecimento')


class Menu(Base):
    __tablename__ = 'menu'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    preco = Column(Numeric(10, 2), nullable=False)
    url_imagem = Column(String, nullable=True)
    descricao = Column(String, nullable=True)
    is_disponivel = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    id_categoria = Column(Integer, ForeignKey('categoria.id'), nullable=False)
    id_estabelecimento = Column(
        Integer, ForeignKey('estabelecimento.id'), nullable=False
    )

    categoria = relationship('Categoria', back_populates='menus')
    estabelecimento = relationship('Estabelecimento', back_populates='menus')
    itens_pedido = relationship('ItemPedido', back_populates='menu')


class Pedido(Base):
    __tablename__ = 'pedido'

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_estabelecimento = Column(
        Integer, ForeignKey('estabelecimento.id'), nullable=False, index=True
    )

    status = Column(String, default='em_preparo')  # 🔥 IMPORTANTE
    created_at = Column(DateTime, server_default=func.now())

    estabelecimento = relationship('Estabelecimento', back_populates='pedidos')

    itens = relationship(
        'ItemPedido', back_populates='pedido', cascade='all, delete-orphan'
    )

    pagamentos = relationship(
        'Pagamento', back_populates='pedido', cascade='all, delete-orphan'
    )


class ItemPedido(Base):
    __tablename__ = 'item_pedido'
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_pedido = Column(Integer, ForeignKey('pedido.id'), nullable=False)
    id_menu = Column(Integer, ForeignKey('menu.id'), nullable=False)
    quantidade = Column(Integer, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    pedido = relationship('Pedido', back_populates='itens')
    menu = relationship('Menu', back_populates='itens_pedido')


class Pagamento(Base):
    __tablename__ = 'pagamento'
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_pedido = Column(Integer, ForeignKey('pedido.id'), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    status_pagamento = Column(String, nullable=False)  # Ex: 'pendente', 'pago'
    data_hora = Column(DateTime, server_default=func.now())

    pedido = relationship('Pedido', back_populates='pagamentos')
