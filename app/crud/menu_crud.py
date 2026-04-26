from app.models.models import Menu


def create_menu(db, menu):

    db_menu = Menu(
        nome=menu.nome,
        preco=menu.preco,
        descricao=menu.descricao,
        url_imagem=menu.url_imagem,
        id_categoria=menu.id_categoria,
        id_estabelecimento=menu.id_estabelecimento,
    )

    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)

    return db_menu


def list_menu(db):
    return db.query(Menu).all()
