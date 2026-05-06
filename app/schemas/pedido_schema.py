from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class ItemPedidoCreate(BaseModel):
    id_menu: int
    quantidade: int


class ItemPedidoResponse(BaseModel):
    id: int
    id_menu: int
    quantidade: int
    subtotal: Decimal

    class Config:
        orm_mode = True


class PedidoCreate(BaseModel):
    id_estabelecimento: int
    itens: list[ItemPedidoCreate]


class PedidoResponse(BaseModel):
    id: int
    id_estabelecimento: int
    created_at: datetime
    itens: list[ItemPedidoResponse] = []

    class Config:
        orm_mode = True
