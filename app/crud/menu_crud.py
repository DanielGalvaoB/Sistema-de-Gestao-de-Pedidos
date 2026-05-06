from sqlalchemy import select
from app.models.models import Menu


def create_menu(db, menu):
    """Criar novo item de menu"""
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
    """Listar todos os itens de menu"""
    return db.query(Menu).all()


def get_menu(db, menu_id: int):
    """Obter item de menu por ID"""
    return db.query(Menu).filter(Menu.id == menu_id).first()


def list_menu_by_categoria(db, categoria_id: int):
    """Listar itens de menu por categoria"""
    return db.query(Menu).filter(Menu.id_categoria == categoria_id).all()


def update_menu(db, menu_id: int, menu_update):
    """Atualizar item de menu"""
    menu = db.get(Menu, menu_id)
    if not menu:
        return None

    update_data = menu_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(menu, field, value)

    db.commit()
    db.refresh(menu)

    return menu


def delete_menu(db, menu_id: int):
    """Deletar item de menu"""
    menu = db.get(Menu, menu_id)
    if not menu:
        return None

    db.delete(menu)
    db.commit()

    return True
