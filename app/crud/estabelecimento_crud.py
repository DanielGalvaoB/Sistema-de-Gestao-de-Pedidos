from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.core.security import hash_password
from app.core.utils import slugify
from app.models.models import CategoriaFinanceira, Estabelecimento, Usuario
from app.schemas.estabelecimento_schema import (
    EstabelecimentoCreate,
    EstabelecimentoUpdate,
)

CATEGORIAS_FINANCEIRAS_PADRAO = [
    ('Vendas', 'entrada', True),
    ('Outras receitas', 'entrada', False),
]


def _slug_unico(db: Session, nome: str) -> str:
    base = slugify(nome)
    slug, n = base, 2
    while db.scalar(
        select(Estabelecimento.id).where(Estabelecimento.slug == slug)
    ):
        slug = f'{base}-{n}'
        n += 1
    return slug


def _email_em_uso(db: Session, email: str, exceto_estab: int | None = None):
    q = select(Estabelecimento.id).where(Estabelecimento.email == email)
    if exceto_estab:
        q = q.where(Estabelecimento.id != exceto_estab)
    return db.scalar(q) is not None


def create_estabelecimento(db: Session, data: EstabelecimentoCreate):
    email = data.email.lower()
    if _email_em_uso(db, email) or db.scalar(
        select(Usuario.id).where(Usuario.email == email)
    ):
        raise ConflictError('Email ja cadastrado')

    est = Estabelecimento(
        nome_loja=data.nome_loja,
        slug=_slug_unico(db, data.nome_loja),
        chave_pix=data.chave_pix,
        nome_titular=data.nome_titular,
        cidade=data.cidade,
        email=email,
    )
    db.add(est)
    db.flush()
    db.add(
        Usuario(
            id_estabelecimento=est.id,
            nome=data.nome_admin or data.nome_titular,
            email=email,
            password_hash=hash_password(data.password),
            perfil='admin',
        )
    )
    for nome, tipo, sistema in CATEGORIAS_FINANCEIRAS_PADRAO:
        db.add(
            CategoriaFinanceira(
                id_estabelecimento=est.id,
                nome=nome,
                tipo=tipo,
                sistema=sistema,
            )
        )
    db.commit()
    db.refresh(est)
    return est


def get_estabelecimento(db: Session, est_id: int) -> Estabelecimento:
    est = db.get(Estabelecimento, est_id)
    if not est:
        raise NotFoundError('Estabelecimento nao encontrado')
    return est


def get_por_slug(db: Session, slug: str) -> Estabelecimento:
    est = db.scalar(
        select(Estabelecimento).where(
            Estabelecimento.slug == slug, Estabelecimento.ativo.is_(True)
        )
    )
    if not est:
        raise NotFoundError('Estabelecimento nao encontrado')
    return est


def update_estabelecimento(
    db: Session, est: Estabelecimento, data: EstabelecimentoUpdate
):
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    if 'email' in update_data:
        update_data['email'] = update_data['email'].lower()
        if _email_em_uso(db, update_data['email'], exceto_estab=est.id):
            raise ConflictError('Email ja cadastrado')

    for key, value in update_data.items():
        setattr(est, key, value)

    db.commit()
    db.refresh(est)
    return est
