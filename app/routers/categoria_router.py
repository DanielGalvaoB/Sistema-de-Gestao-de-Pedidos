from fastapi import APIRouter, status

from app.crud import categoria_crud
from app.dependencies.auth_dep import Admin, CurrentUser, DbSession
from app.schemas.categoria_schema import (
    CategoriaCreate,
    CategoriaPut,
    CategoriaResponse,
    CategoriaUpdate,
)

router = APIRouter(prefix='/categorias', tags=['categorias'])


@router.post(
    path='/',
    status_code=status.HTTP_201_CREATED,
    response_model=CategoriaResponse,
)
def create_categoria(categoria: CategoriaCreate, db: DbSession, user: Admin):
    return categoria_crud.create_categoria(
        db, user.id_estabelecimento, categoria
    )


@router.get(path='/', response_model=list[CategoriaResponse])
def list_categorias(db: DbSession, user: CurrentUser):
    return categoria_crud.list_categorias(db, user.id_estabelecimento)


@router.get(path='/{categoria_id}', response_model=CategoriaResponse)
def get_category(categoria_id: int, db: DbSession, user: CurrentUser):
    return categoria_crud.get_categoria(
        db, user.id_estabelecimento, categoria_id
    )


@router.put(path='/{categoria_id}', response_model=CategoriaResponse)
def categoria_update(
    categoria_id: int, categoria: CategoriaPut, db: DbSession, user: Admin
):
    return categoria_crud.update_categoria(
        db, user.id_estabelecimento, categoria_id, categoria, parcial=False
    )


@router.patch(path='/{categoria_id}', response_model=CategoriaResponse)
def elemento_categoria_update(
    categoria_id: int, categoria: CategoriaUpdate, db: DbSession, user: Admin
):
    return categoria_crud.update_categoria(
        db, user.id_estabelecimento, categoria_id, categoria, parcial=True
    )


@router.delete(path='/{categoria_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_category(categoria_id: int, db: DbSession, user: Admin):
    categoria_crud.delete_category(db, user.id_estabelecimento, categoria_id)
