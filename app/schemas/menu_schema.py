from decimal import Decimal

from pydantic import BaseModel


class MenuCreate(BaseModel):
    nome: str
    preco: Decimal
    descricao: str | None = None
    url_imagem: str | None = None
    id_categoria: int
    id_estabelecimento: int


class MenuResponse(BaseModel):
    id: int
    nome: str
    preco: Decimal

    class Config:
        orm_mode = True


class MenuUpdate(BaseModel):
    nome: str | None = None
    preco: Decimal | None = None
    descricao: str | None = None
    url_imagem: str | None = None
    id_categoria: int | None = None
    id_estabelecimento: int | None = None
