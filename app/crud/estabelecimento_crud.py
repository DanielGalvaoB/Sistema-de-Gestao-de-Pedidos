from app.models.models import Estabelecimento
from sqlalchemy.exc import IntegrityError

def create_estabelecimento(db, data):
    db_est = Estabelecimento(
        nome_loja=data.nome_loja,
        chave_pix=data.chave_pix,
        nome_titular=data.nome_titular,
        email=data.email,
        password_hash=data.password
    )

    db.add(db_est)

    try:
        db.commit()
        db.refresh(db_est)
        return db_est

    except IntegrityError:
        db.rollback()
        return None


def list_estabelecimentos(db):
    return db.query(Estabelecimento).all()


def get_estabelecimento(db, est_id: int):
    return db.get(Estabelecimento, est_id)


def update_estabelecimento(db, est_id: int, data):
    est = db.get(Estabelecimento, est_id)

    if not est:
        return None

    update_data = data.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(est, key, value)

    db.commit()
    db.refresh(est)

    return est


def delete_estabelecimento(db, est_id: int):
    est = db.get(Estabelecimento, est_id)

    if not est:
        return None

    db.delete(est)
    db.commit()

    return True
