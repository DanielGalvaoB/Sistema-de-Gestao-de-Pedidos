from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import estabelecimento_crud
from app.dependencies.db_dep import get_db
from app.schemas.estabelecimento_schema import (
    EstabelecimentoCreate,
    EstabelecimentoResponse,
    EstabelecimentoUpdate,
)

router = APIRouter(prefix='/estabelecimentos')


@router.post(
    path="/", 
    response_model=EstabelecimentoResponse,
    status_code=status.HTTP_201_CREATED)
def create(data: EstabelecimentoCreate, db: Session = Depends(get_db)):
    est = estabelecimento_crud.create_estabelecimento(db, data)

    if not est:
        raise HTTPException(
            status_code=400,
            detail="Email já cadastrado"
        )

    return est

@router.get(    
    path='/', 
    response_model=list[EstabelecimentoResponse],
    status_code=status.HTTP_200_OK
    )
def list_all(db: Session = Depends(get_db)):
    return estabelecimento_crud.list_estabelecimentos(db)


@router.get('/{id}', response_model=EstabelecimentoResponse)
def get(id: int, db: Session = Depends(get_db)):
    est = estabelecimento_crud.get_estabelecimento(db, id)

    if not est:
        raise HTTPException(404, 'not found')

    return est


@router.patch(
    path='/{id}', 
    response_model=EstabelecimentoResponse,
    status_code=status.HTTP_200_OK)
def update(
    id: int, data: EstabelecimentoUpdate, db: Session = Depends(get_db)
):
    updated = estabelecimento_crud.update_estabelecimento(db, id, data)

    if not updated:
        raise HTTPException(404, 'not found')

    return updated


@router.delete('/{id}', status_code=204)
def delete(id: int, db: Session = Depends(get_db)):
    deleted = estabelecimento_crud.delete_estabelecimento(db, id)

    if not deleted:
        raise HTTPException(404, 'not found')
