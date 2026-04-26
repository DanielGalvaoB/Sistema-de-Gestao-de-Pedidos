from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import categoria_crud
from app.dependencies.db_dep import get_db
from app.schemas.categoria_schema import CategoriaCreate

router = APIRouter(prefix='/categorias')


@router.post('/')
def create_categoria(
    categoria: CategoriaCreate, db: Session = Depends(get_db)
):
    return categoria_crud.create_categoria(db, categoria)


@router.get('/')
def list_categorias(db: Session = Depends(get_db)):
    return categoria_crud.list_categorias(db)
