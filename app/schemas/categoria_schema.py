from pydantic import BaseModel, Field

from app.schemas.common import NonEmptyStr, ORMModel


class CategoriaCreate(BaseModel):
    nome: NonEmptyStr = Field(max_length=80)
    ordem: int = 0


class CategoriaPut(BaseModel):
    """Substituicao completa (PUT): todos os campos obrigatorios."""

    nome: NonEmptyStr = Field(max_length=80)
    ordem: int = 0
    ativo: bool = True


class CategoriaUpdate(BaseModel):
    """Atualizacao parcial (PATCH)."""

    nome: NonEmptyStr | None = Field(default=None, max_length=80)
    ordem: int | None = None
    ativo: bool | None = None


class CategoriaResponse(ORMModel):
    id: int
    nome: str
    ordem: int
    ativo: bool
