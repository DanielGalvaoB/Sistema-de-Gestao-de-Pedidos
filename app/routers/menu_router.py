from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import menu_crud
from app.dependencies.db_dep import get_db
from app.schemas.menu_schema import MenuCreate, MenuUpdate, MenuResponse

router = APIRouter(prefix='/menu')


@router.post(
    path='/',
    status_code=status.HTTP_201_CREATED,
    response_model=MenuResponse,
)
def create_menu(menu: MenuCreate, db: Session = Depends(get_db)):
    """Criar novo item de menu"""
    return menu_crud.create_menu(db, menu)


@router.get(
    path='/',
    response_model=list[MenuResponse],
    status_code=status.HTTP_200_OK,
)
def list_menu(db: Session = Depends(get_db)):
    """Listar todos os itens de menu"""
    return menu_crud.list_menu(db)


@router.get(
    path='/{menu_id}',
    response_model=MenuResponse,
    status_code=status.HTTP_200_OK,
)
def get_menu(menu_id: int, db: Session = Depends(get_db)):
    """Obter item de menu específico"""
    menu = menu_crud.get_menu(db, menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Item de menu não encontrado'
        )
    return menu


@router.put(
    path='/{menu_id}',
    response_model=MenuResponse,
    status_code=status.HTTP_200_OK,
)
def update_menu(
    menu_id: int,
    menu_update: MenuUpdate,
    db: Session = Depends(get_db)
):
    """Atualizar item de menu"""
    menu = menu_crud.update_menu(db, menu_id, menu_update)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Item de menu não encontrado'
        )
    return menu


@router.delete(
    path='/{menu_id}',
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_menu(menu_id: int, db: Session = Depends(get_db)):
    """Deletar item de menu"""
    result = menu_crud.delete_menu(db, menu_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Item de menu não encontrado'
        )
    return None
