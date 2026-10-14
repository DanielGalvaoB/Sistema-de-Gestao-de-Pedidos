from fastapi import APIRouter, File, Response, UploadFile, status

from app.config import settings
from app.crud import menu_crud
from app.dependencies.auth_dep import Admin, CurrentUser, DbSession
from app.schemas.menu_schema import (
    HistoricoPrecoResponse,
    MenuCreate,
    MenuResponse,
    MenuUpdate,
)

router = APIRouter(prefix='/menu', tags=['menu'])


@router.post(
    path='/', status_code=status.HTTP_201_CREATED, response_model=MenuResponse
)
def create_menu(menu: MenuCreate, db: DbSession, user: Admin):
    return menu_crud.create_menu(db, user.id_estabelecimento, menu)


@router.get(path='/', response_model=list[MenuResponse])
def list_menu(
    db: DbSession,
    user: CurrentUser,
    busca: str | None = None,
    id_categoria: int | None = None,
    disponivel: bool | None = None,
    incluir_inativos: bool = False,
):
    # Sempre devolve uma lista (vazia quando nao ha produtos)
    return menu_crud.list_menu(
        db,
        user.id_estabelecimento,
        busca=busca,
        id_categoria=id_categoria,
        disponivel=disponivel,
        incluir_inativos=incluir_inativos,
    )


@router.get(path='/{menu_id}', response_model=MenuResponse)
def get_menu(menu_id: int, db: DbSession, user: CurrentUser):
    return menu_crud.get_menu(db, user.id_estabelecimento, menu_id)


@router.get(
    path='/{menu_id}/historico-precos',
    response_model=list[HistoricoPrecoResponse],
)
def historico_precos(menu_id: int, db: DbSession, user: CurrentUser):
    return menu_crud.get_menu(
        db, user.id_estabelecimento, menu_id
    ).historico_precos


@router.post(path='/{menu_id}/imagem', response_model=MenuResponse)
def enviar_imagem(
    menu_id: int,
    db: DbSession,
    user: Admin,
    arquivo: UploadFile = File(description='JPG, PNG ou WebP'),
):
    """Envia a foto do produto (substitui a anterior)."""
    # Le no maximo o limite + 1 byte para detectar arquivos grandes demais
    conteudo = arquivo.file.read(settings.MAX_UPLOAD_MB * 1024 * 1024 + 1)
    return menu_crud.definir_imagem(
        db, user.id_estabelecimento, menu_id, conteudo
    )


@router.delete(path='/{menu_id}/imagem', response_model=MenuResponse)
def remover_imagem(menu_id: int, db: DbSession, user: Admin):
    return menu_crud.remover_imagem(db, user.id_estabelecimento, menu_id)


@router.patch(path='/{menu_id}', response_model=MenuResponse)
def update_menu(menu_id: int, menu: MenuUpdate, db: DbSession, user: Admin):
    return menu_crud.update_menu(
        db, user.id_estabelecimento, menu, menu_id, user.id
    )


@router.delete(path='/{menu_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(menu_id: int, db: DbSession, user: Admin, response: Response):
    """Exclui produtos nunca vendidos; os ja vendidos sao desativados."""
    resultado = menu_crud.menu_delete(db, user.id_estabelecimento, menu_id)
    response.headers['X-Resultado'] = resultado
