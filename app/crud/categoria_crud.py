from sqlalchemy import select

from app.models.models import Categoria


# create
def create_categoria(db, categoria):

    db_categoria = Categoria(nome=categoria.nome)

    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)

    return db_categoria


# read_all
def list_categorias(db):
    return db.scalars(select(Categoria)).all()


# # readForID
# def get_categoria(db, categoria_id: int):
#     return db.query(Categoria, categoria_id)


# update
def update_categoria(db, id_categoria: int, categoria_update):
    categoria = db.get(Categoria, id_categoria)

    if not categoria:
        return None

    update_data = categoria_update.model_dump()

    for field, value in update_data.items():
        setattr(categoria, field, value)

    db.commit()
    db.refresh(categoria)

    return categoria

def update_elemento_categoria(db, id_categoria: int, categoria_update):
    categoria = db.get(Categoria, id_categoria)

    if not categoria:
        return None

    update_data = categoria_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(categoria, field, value)

    db.commit()
    db.refresh(categoria)

    return categoria

#delete
def delete_category(db, categoria_id:int):
    categoria = db.get(Categoria, categoria_id)
    
    if not categoria :
        return None
    
    db.delete(categoria)
    db.commit()
    
    return True