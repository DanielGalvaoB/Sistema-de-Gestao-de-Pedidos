from datetime import date

from fastapi import APIRouter, status

from app.core.utils import periodo_utc
from app.crud import financeiro_crud
from app.dependencies.auth_dep import DbSession, Financeiro
from app.schemas.financeiro_schema import (
    CancelamentoRequest,
    CategoriaFinanceiraCreate,
    CategoriaFinanceiraResponse,
    CategoriaFinanceiraUpdate,
    MovimentacaoCreate,
    MovimentacaoResponse,
    MovimentacaoUpdate,
)

router = APIRouter(prefix='/financeiro', tags=['financeiro'])


@router.get('/categorias', response_model=list[CategoriaFinanceiraResponse])
def list_categorias(db: DbSession, user: Financeiro):
    return financeiro_crud.list_categorias(db, user.id_estabelecimento)


@router.post(
    '/categorias',
    response_model=CategoriaFinanceiraResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_categoria(
    data: CategoriaFinanceiraCreate, db: DbSession, user: Financeiro
):
    return financeiro_crud.create_categoria(db, user.id_estabelecimento, data)


@router.patch(
    '/categorias/{cat_id}', response_model=CategoriaFinanceiraResponse
)
def update_categoria(
    cat_id: int,
    data: CategoriaFinanceiraUpdate,
    db: DbSession,
    user: Financeiro,
):
    return financeiro_crud.update_categoria(
        db, user.id_estabelecimento, cat_id, data
    )


@router.get('/movimentacoes', response_model=list[MovimentacaoResponse])
def list_movimentacoes(
    db: DbSession,
    user: Financeiro,
    inicio: date | None = None,
    fim: date | None = None,
    id_categoria: int | None = None,
    metodo: str | None = None,
    status_mov: str | None = None,
):
    ini = end = None
    if inicio and fim:
        ini, end = periodo_utc(inicio, fim)
    movs = financeiro_crud.list_movimentacoes(
        db,
        user.id_estabelecimento,
        ini,
        end,
        id_categoria,
        metodo,
        status_mov,
    )
    return [financeiro_crud.mov_to_dict(m) for m in movs]


@router.post(
    '/movimentacoes',
    response_model=MovimentacaoResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_movimentacao(
    data: MovimentacaoCreate, db: DbSession, user: Financeiro
):
    mov = financeiro_crud.create_movimentacao(
        db, user.id_estabelecimento, data, user.id
    )
    return financeiro_crud.mov_to_dict(mov)


@router.patch('/movimentacoes/{mov_id}', response_model=MovimentacaoResponse)
def update_movimentacao(
    mov_id: int, data: MovimentacaoUpdate, db: DbSession, user: Financeiro
):
    mov = financeiro_crud.update_movimentacao(
        db, user.id_estabelecimento, mov_id, data
    )
    return financeiro_crud.mov_to_dict(mov)


@router.post(
    '/movimentacoes/{mov_id}/cancelar', response_model=MovimentacaoResponse
)
def cancelar_movimentacao(
    mov_id: int, data: CancelamentoRequest, db: DbSession, user: Financeiro
):
    """Cancela com historico (lancamentos nunca sao apagados)."""
    mov = financeiro_crud.cancelar_movimentacao(
        db, user.id_estabelecimento, mov_id, data.motivo, user.id
    )
    return financeiro_crud.mov_to_dict(mov)
