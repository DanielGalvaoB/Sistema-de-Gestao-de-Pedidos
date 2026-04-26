from pydantic import BaseModel


class ItemPedidoCreate(BaseModel):
    id_menu: int
    quantidade: int


class PedidoCreate(BaseModel):
    id_estabelecimento: int
    itens: list[ItemPedidoCreate]
