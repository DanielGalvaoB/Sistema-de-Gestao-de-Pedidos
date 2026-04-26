from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import pedido_crud
from app.dependencies.db_dep import get_db
from app.schemas.pedido_schema import PedidoCreate

router = APIRouter(prefix='/pedidos')


@router.post('/')
def create_pedido(pedido: PedidoCreate, db: Session = Depends(get_db)):
    return pedido_crud.create_pedido(db, pedido)
