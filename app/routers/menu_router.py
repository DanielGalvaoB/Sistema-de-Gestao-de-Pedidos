from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import menu_crud
from app.dependencies.db_dep import get_db
from app.models.models import Menu
from app.schemas.menu_schema import MenuCreate, MenuResponse, MenuUpdate

router = APIRouter(prefix='/menu')


@router.post(
    path='/', status_code=status.HTTP_201_CREATED, response_model=MenuResponse
)
def create_menu(menu: MenuCreate, db: Session = Depends(get_db)):
    newMenu = menu_crud.create_menu(db, menu)
    return newMenu


@router.get(
    path='/', status_code=status.HTTP_200_OK, response_model=list[MenuResponse]
)
def list_menu(db: Session = Depends(get_db)):
    listMenu = menu_crud.list_menu(db)
    if not listMenu:
        return None

    return listMenu


@router.get(
    path='/{menu_id}',
    status_code=status.HTTP_200_OK,
    response_model=MenuResponse,
)
def get_menu(menu_id: int, db: Session = Depends(get_db)):
    get_response = db.get(Menu, menu_id)

    if not get_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='menu not found'
        )
    return get_response


@router.patch(
    path='/{menu_id}',
    response_model=MenuResponse,
    status_code=status.HTTP_200_OK,
)
def update_menu(menu_id: int, menu: MenuUpdate, db: Session = Depends(get_db)):
    update = menu_crud.update_menu(db, menu, menu_id)

    if not update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='menu not found'
        )
    return update


@router.delete(
    path='/{menu_id}',
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_menu(menu_id: int, db: Session = Depends(get_db)):
    menu_delete = menu_crud.menu_delete(db, menu_id)

    if not menu_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='menu not found'
        )
    return menu_delete
