from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.models.models import Categoria, Menu


def _nome_livre(db: Session, id_estab: int, nome: str, exceto: int = 0):
    existe = db.scalar(
        select(Categoria.id).where(
            Categoria.id_estabelecimento == id_estab,
            func.lower(Categoria.nome) == nome.lower(),
            Categoria.id != exceto,
        )
    )
    if existe:
        raise ConflictError('Ja existe uma categoria com este nome')


# create
def create_categoria(db: Session, id_estab: int, categoria):
    _nome_livre(db, id_estab, categoria.nome)
    db_categoria = Categoria(
        id_estabelecimento=id_estab, nome=categoria.nome, ordem=categoria.ordem
    )

    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)

    return db_categoria


# read_all
def list_categorias(db: Session, id_estab: int, apenas_ativas=False):
    q = select(Categoria).where(Categoria.id_estabelecimento == id_estab)
    if apenas_ativas:
        q = q.where(Categoria.ativo.is_(True))
    return db.scalars(q.order_by(Categoria.ordem, Categoria.nome)).all()


# readForID
def get_categoria(db: Session, id_estab: int, categoria_id: int) -> Categoria:
    categoria = db.get(Categoria, categoria_id)
    if not categoria or categoria.id_estabelecimento != id_estab:
        raise NotFoundError('Categoria nao encontrada')
    return categoria


# update (PUT substitui tudo; PATCH envia exclude_unset)
def update_categoria(
    db: Session, id_estab: int, id_categoria: int, categoria_update, parcial
):
    categoria = get_categoria(db, id_estab, id_categoria)

    update_data = categoria_update.model_dump(
        exclude_unset=parcial, exclude_none=parcial
    )
    if 'nome' in update_data:
        _nome_livre(db, id_estab, update_data['nome'], exceto=categoria.id)

    for field, value in update_data.items():
        setattr(categoria, field, value)

    db.commit()
    db.refresh(categoria)

    return categoria


# delete
def delete_category(db: Session, id_estab: int, categoria_id: int):
    categoria = get_categoria(db, id_estab, categoria_id)

    em_uso = db.scalar(
        select(func.count(Menu.id)).where(Menu.id_categoria == categoria.id)
    )
    if em_uso:
        raise ConflictError(
            'Categoria possui produtos vinculados; '
            'desative-a em vez de excluir'
        )

    db.delete(categoria)
    db.commit()
