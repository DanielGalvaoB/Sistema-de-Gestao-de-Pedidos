from pydantic import BaseModel


class CategoriaCreate(BaseModel):
    nome: str


class CategoriaResponse(BaseModel):
    id: int
    nome: str

    class Config:
        orm_mode = True
