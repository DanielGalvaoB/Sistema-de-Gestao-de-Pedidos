from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import BusinessRuleError, NotFoundError
from app.core.imagens import remover_imagem_local, salvar_imagem_produto
from app.core.utils import q2
from app.crud.categoria_crud import get_categoria
from app.models.models import HistoricoPreco, ItemPedido, Menu


def _validar_categoria(db: Session, id_estab: int, id_categoria: int):
    try:
        get_categoria(db, id_estab, id_categoria)
    except NotFoundError as exc:
        raise BusinessRuleError('Categoria informada nao existe') from exc


# create
def create_menu(db: Session, id_estab: int, menu):
    _validar_categoria(db, id_estab, menu.id_categoria)

    db_menu = Menu(
        id_estabelecimento=id_estab, **menu.model_dump(), ativo=True
    )
    db_menu.preco = q2(db_menu.preco)

    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)

    return db_menu


# read
def list_menu(
    db: Session,
    id_estab: int,
    busca: str | None = None,
    id_categoria: int | None = None,
    disponivel: bool | None = None,
    incluir_inativos: bool = False,
):
    q = select(Menu).where(Menu.id_estabelecimento == id_estab)
    if not incluir_inativos:
        q = q.where(Menu.ativo.is_(True))
    if busca:
        termo = f'%{busca.lower()}%'
        q = q.where(
            or_(
                func.lower(Menu.nome).like(termo),
                func.lower(Menu.descricao).like(termo),
            )
        )
    if id_categoria is not None:
        q = q.where(Menu.id_categoria == id_categoria)
    if disponivel is not None:
        q = q.where(Menu.is_disponivel.is_(disponivel))
    return db.scalars(q.order_by(Menu.nome)).all()


def get_menu(db: Session, id_estab: int, id_menu: int) -> Menu:
    menu = db.get(Menu, id_menu)
    if not menu or menu.id_estabelecimento != id_estab:
        raise NotFoundError('Produto nao encontrado')
    return menu


# update
def update_menu(db: Session, id_estab: int, menu_data, id_menu: int, user_id):
    db_menu = get_menu(db, id_estab, id_menu)

    update_data = menu_data.model_dump(exclude_unset=True)
    for obrigatorio in (
        'nome',
        'preco',
        'id_categoria',
        'is_disponivel',
        'ativo',
    ):
        if obrigatorio in update_data and update_data[obrigatorio] is None:
            raise BusinessRuleError(f'O campo {obrigatorio} nao pode ser nulo')
    if 'id_categoria' in update_data:
        _validar_categoria(db, id_estab, update_data['id_categoria'])

    if 'preco' in update_data:
        novo = q2(update_data['preco'])
        update_data['preco'] = novo
        if novo != q2(db_menu.preco):
            # Itens de pedidos guardam o proprio preco; aqui so registramos
            # o historico do cardapio.
            db.add(
                HistoricoPreco(
                    id_menu=db_menu.id,
                    preco_anterior=q2(db_menu.preco),
                    preco_novo=novo,
                    id_usuario=user_id,
                )
            )

    for key, value in update_data.items():
        setattr(db_menu, key, value)

    db.commit()
    db.refresh(db_menu)

    return db_menu


def definir_imagem(db: Session, id_estab: int, id_menu: int, conteudo: bytes):
    menu = get_menu(db, id_estab, id_menu)
    nova = salvar_imagem_produto(conteudo, id_estab, menu.id)
    antiga = menu.url_imagem
    menu.url_imagem = nova
    db.commit()
    remover_imagem_local(antiga)
    db.refresh(menu)
    return menu


def remover_imagem(db: Session, id_estab: int, id_menu: int):
    menu = get_menu(db, id_estab, id_menu)
    antiga = menu.url_imagem
    menu.url_imagem = None
    db.commit()
    remover_imagem_local(antiga)
    db.refresh(menu)
    return menu


# delete: remove de fato apenas produtos nunca vendidos; os demais sao
# desativados para preservar o historico dos pedidos.
def menu_delete(db: Session, id_estab: int, id_menu: int) -> str:
    menu = get_menu(db, id_estab, id_menu)
    vendido = db.scalar(
        select(func.count(ItemPedido.id)).where(ItemPedido.id_menu == menu.id)
    )
    if vendido:
        menu.ativo = False
        menu.is_disponivel = False
        db.commit()
        return 'desativado'

    db.delete(menu)
    db.commit()
    return 'excluido'
