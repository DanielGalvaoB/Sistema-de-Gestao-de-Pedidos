from pydantic import BaseModel


class CategoriaCreate(BaseModel):
    nome: str


class CategoriaUpdate(BaseModel):
    nome: str | None = None


class CategoriaResponse(BaseModel):
    id: int
    nome: str

    class Config:
        orm_mode = True
