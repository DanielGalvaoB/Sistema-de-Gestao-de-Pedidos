from app.models.models import Menu


# create
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


# read
def list_menu(db):
    return db.query(Menu).all()


# update
def update_menu(db, menu_data, id_menu: int):
    db_menu = db.query(Menu).filter(Menu.id == id_menu).first()

    if not db_menu:
        return None

    update_data = menu_data.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_menu, key, value)

    db.commit()
    db.refresh(db_menu)

    return db_menu


# delete
def menu_delete(db, id_menu: int):
    menu = db.get(Menu, id_menu)
    if not menu:
        return None

    db.delete(menu)
    db.commit()

    return True
