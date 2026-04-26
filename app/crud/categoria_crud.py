from app.models.models import Categoria


def create_categoria(db, categoria):

    db_categoria = Categoria(nome=categoria.nome)

    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)

    return db_categoria


def list_categorias(db):
    return db.query(Categoria).all()
