from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.errors import ConflictError, NotFoundError
from app.core.utils import novo_token
from app.models.models import STATUS_SESSAO_ABERTA, Mesa, SessaoAtendimento


def _numero_livre(db: Session, id_estab: int, numero: str, exceto: int = 0):
    existe = db.scalar(
        select(Mesa.id).where(
            Mesa.id_estabelecimento == id_estab,
            func.lower(Mesa.numero) == numero.lower(),
            Mesa.id != exceto,
        )
    )
    if existe:
        raise ConflictError('Ja existe uma mesa com este numero')


def create_mesa(db: Session, id_estab: int, data):
    _numero_livre(db, id_estab, data.numero)
    mesa = Mesa(
        id_estabelecimento=id_estab,
        numero=data.numero,
        capacidade=data.capacidade,
        token=novo_token(),
    )
    db.add(mesa)
    db.commit()
    db.refresh(mesa)
    return mesa


def list_mesas(db: Session, id_estab: int, incluir_inativas=False):
    q = select(Mesa).where(Mesa.id_estabelecimento == id_estab)
    if not incluir_inativas:
        q = q.where(Mesa.ativo.is_(True))
    mesas = db.scalars(q).all()
    # Ordena "2" antes de "10"
    return sorted(
        mesas,
        key=lambda m: (
            not m.numero.isdigit(),
            int(m.numero) if m.numero.isdigit() else 0,
            m.numero,
        ),
    )


def get_mesa(db: Session, id_estab: int, mesa_id: int) -> Mesa:
    mesa = db.get(Mesa, mesa_id)
    if not mesa or mesa.id_estabelecimento != id_estab:
        raise NotFoundError('Mesa nao encontrada')
    return mesa


def get_mesa_por_token(db: Session, id_estab: int, token: str) -> Mesa:
    mesa = db.scalar(
        select(Mesa).where(
            Mesa.token == token,
            Mesa.id_estabelecimento == id_estab,
            Mesa.ativo.is_(True),
        )
    )
    if not mesa:
        raise NotFoundError('Mesa nao encontrada ou desativada')
    return mesa


def sessao_aberta_da_mesa(db: Session, mesa_id: int):
    return db.scalar(
        select(SessaoAtendimento).where(
            SessaoAtendimento.id_mesa == mesa_id,
            SessaoAtendimento.status.in_(STATUS_SESSAO_ABERTA),
        )
    )


def update_mesa(db: Session, mesa: Mesa, data):
    update_data = data.model_dump(exclude_unset=True)
    if update_data.get('numero'):
        _numero_livre(
            db, mesa.id_estabelecimento, update_data['numero'], mesa.id
        )
    elif 'numero' in update_data:
        update_data.pop('numero')
    if update_data.get('ativo') is False and sessao_aberta_da_mesa(
        db, mesa.id
    ):
        raise ConflictError(
            'A mesa possui uma conta aberta; '
            'encerre a conta antes de desativar'
        )
    if 'ativo' in update_data and update_data['ativo'] is None:
        update_data.pop('ativo')
    for key, value in update_data.items():
        setattr(mesa, key, value)
    db.commit()
    db.refresh(mesa)
    return mesa


def regenerar_token(db: Session, mesa: Mesa):
    mesa.token = novo_token()
    db.commit()
    db.refresh(mesa)
    return mesa


def url_cardapio(slug: str, mesa_token: str | None = None) -> str:
    base = f'{settings.FRONTEND_URL.rstrip("/")}/c/{slug}'
    return f'{base}?mesa={mesa_token}' if mesa_token else base
