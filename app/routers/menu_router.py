from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import menu_crud
from app.dependencies.db_dep import get_db
from app.schemas.menu_schema import MenuCreate

router = APIRouter(prefix='/menu')


@router.post('/')
def create_menu(menu: MenuCreate, db: Session = Depends(get_db)):
    return menu_crud.create_menu(db, menu)


@router.get('/')
def list_menu(db: Session = Depends(get_db)):
    return menu_crud.list_menu(db)
