from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import BusinessRuleError, ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.models import Usuario
from app.schemas.usuario_schema import UsuarioCreate, UsuarioUpdate


def autenticar(db: Session, email: str, password: str) -> Usuario | None:
    user = db.scalar(select(Usuario).where(Usuario.email == email.lower()))
    if not user or not verify_password(password, user.password_hash):
        return None
    if not user.ativo or not user.estabelecimento.ativo:
        return None
    return user


def list_usuarios(db: Session, id_estab: int):
    return db.scalars(
        select(Usuario)
        .where(Usuario.id_estabelecimento == id_estab)
        .order_by(Usuario.nome)
    ).all()


def get_usuario(db: Session, id_estab: int, user_id: int) -> Usuario:
    user = db.get(Usuario, user_id)
    if not user or user.id_estabelecimento != id_estab:
        raise NotFoundError('Usuario nao encontrado')
    return user


def _email_livre(db: Session, email: str, exceto: int | None = None):
    q = select(Usuario.id).where(Usuario.email == email)
    if exceto:
        q = q.where(Usuario.id != exceto)
    if db.scalar(q):
        raise ConflictError('Email ja cadastrado')


def create_usuario(db: Session, id_estab: int, data: UsuarioCreate):
    email = data.email.lower()
    _email_livre(db, email)
    user = Usuario(
        id_estabelecimento=id_estab,
        nome=data.nome,
        email=email,
        password_hash=hash_password(data.password),
        perfil=data.perfil,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _admins_ativos(db: Session, id_estab: int) -> int:
    return db.scalar(
        select(func.count(Usuario.id)).where(
            Usuario.id_estabelecimento == id_estab,
            Usuario.perfil == 'admin',
            Usuario.ativo.is_(True),
        )
    )


def update_usuario(db: Session, user: Usuario, data: UsuarioUpdate):
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    if 'email' in update_data:
        update_data['email'] = update_data['email'].lower()
        _email_livre(db, update_data['email'], exceto=user.id)
    if 'password' in update_data:
        update_data['password_hash'] = hash_password(
            update_data.pop('password')
        )

    perde_admin = user.perfil == 'admin' and (
        update_data.get('perfil', 'admin') != 'admin'
        or update_data.get('ativo') is False
    )
    if perde_admin and _admins_ativos(db, user.id_estabelecimento) <= 1:
        raise BusinessRuleError(
            'O estabelecimento precisa de pelo menos um administrador ativo'
        )

    for key, value in update_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def alterar_senha(db: Session, user: Usuario, atual: str, nova: str):
    if not verify_password(atual, user.password_hash):
        raise BusinessRuleError('Senha atual incorreta')
    user.password_hash = hash_password(nova)
    db.commit()
