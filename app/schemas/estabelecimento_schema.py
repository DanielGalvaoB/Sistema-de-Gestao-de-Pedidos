from pydantic import BaseModel, EmailStr


class EstabelecimentoCreate(BaseModel):
    nome_loja: str
    chave_pix: str
    nome_titular: str
    email: EmailStr
    password: str


class EstabelecimentoResponse(BaseModel):
    id: int
    nome_loja: str
    email: str

    class Config:
        orm_mode = True


class EstabelecimentoUpdate(BaseModel):
    nome_loja: str | None = None
    chave_pix: str | None = None
    nome_titular: str | None = None
    email: EmailStr | None = None
    password: str | None = None
