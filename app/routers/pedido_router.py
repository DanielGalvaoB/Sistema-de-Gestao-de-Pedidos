from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import pedido_crud
from app.dependencies.db_dep import get_db
from app.schemas.pedido_schema import PedidoCreate, PedidoResponse

router = APIRouter(prefix='/pedidos')


@router.post(
    path='/',
    status_code=status.HTTP_201_CREATED,
    response_model=PedidoResponse,
)
def create_pedido(pedido: PedidoCreate, db: Session = Depends(get_db)):
    """Criar novo pedido"""
    return pedido_crud.create_pedido(db, pedido)


@router.get(
    path='/',
    response_model=list[PedidoResponse],
    status_code=status.HTTP_200_OK,
)
def list_pedidos(db: Session = Depends(get_db)):
    """Listar todos os pedidos"""
    return pedido_crud.list_pedidos(db)


@router.get(
    path='/{pedido_id}',
    response_model=PedidoResponse,
    status_code=status.HTTP_200_OK,
)
def get_pedido(pedido_id: int, db: Session = Depends(get_db)):
    """Obter pedido específico"""
    pedido = pedido_crud.get_pedido(db, pedido_id)
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Pedido não encontrado'
        )
    return pedido


@router.delete(
    path='/{pedido_id}',
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_pedido(pedido_id: int, db: Session = Depends(get_db)):
    """Deletar/cancelar um pedido"""
    result = pedido_crud.delete_pedido(db, pedido_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Pedido não encontrado'
        )
    return None
