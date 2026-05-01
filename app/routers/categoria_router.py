from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import categoria_crud
from app.dependencies.db_dep import get_db
from app.models.models import Categoria
from app.schemas.categoria_schema import (
    CategoriaCreate,
    CategoriaResponse,
    CategoriaUpdate,
)

router = APIRouter(prefix='/categorias')


@router.post(
    path='/',
    status_code=status.HTTP_201_CREATED,
    response_model=CategoriaResponse,
)
def create_categoria(
    categoria: CategoriaCreate, db: Session = Depends(get_db)
):

    new_categoria = categoria_crud.create_categoria(db, categoria)
    return new_categoria


@router.get(
    path='/',
    response_model=list[CategoriaResponse],
    status_code=status.HTTP_200_OK,
)
def list_categorias(
    db: Session = Depends(get_db),
):
    return categoria_crud.list_categorias(db)


@router.get(
    path='/{categoria_id}',
    response_model=CategoriaResponse,
    status_code=status.HTTP_200_OK,
)
def get_category(
    categoria_id: int,
    db: Session = Depends(get_db),
):
    get_response = db.get(Categoria, categoria_id)

    return get_response


@router.put(
    path='/{categoria_id}',
    response_model=CategoriaResponse,
    status_code=status.HTTP_200_OK,
)
def categoria_update(
    categoria_id: int,
    categoria: CategoriaUpdate,
    db: Session = Depends(get_db),
):
    db_categoria = categoria_crud.update_categoria(db, categoria_id, categoria)

    if not db_categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='categoria not found'
        )

    return db_categoria


@router.patch(
    path='/{categoria_id}',
    response_model=CategoriaResponse,
    status_code=status.HTTP_200_OK,
)
def elemento_categoria_update(
    categoria_id: int,
    categoria: CategoriaUpdate,
    db: Session = Depends(get_db),
):
    db_categoria = categoria_crud.update_elemento_categoria(db, categoria_id, categoria)

    if not db_categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='categoria not found'
        )

    return db_categoria


@router.delete(
    path=('/{categoria_id}'),
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_category(
    categoria_id: int,
    db: Session = Depends(get_db),
):
    deletar = categoria_crud.delete_category(db, categoria_id)
    
    if not deletar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='category not found'
        )
    
    return deletar