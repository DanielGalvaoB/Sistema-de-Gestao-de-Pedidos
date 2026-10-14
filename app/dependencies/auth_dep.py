from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.dependencies.db_dep import get_db
from app.models.models import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')

DbSession = Annotated[Session, Depends(get_db)]


def usuario_do_token(db: Session, token: str) -> Usuario | None:
    user_id = decode_access_token(token)
    if user_id is None:
        return None
    user = db.get(Usuario, user_id)
    if not user or not user.ativo or not user.estabelecimento.ativo:
        return None
    return user


def get_current_user(
    db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]
) -> Usuario:
    user = usuario_do_token(db, token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Credenciais invalidas ou expiradas',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    return user


def require_roles(*perfis: str):
    """Permite o acesso aos perfis informados (admin sempre permitido)."""

    def _dep(user: Annotated[Usuario, Depends(get_current_user)]) -> Usuario:
        if user.perfil != 'admin' and user.perfil not in perfis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Seu perfil nao tem permissao para esta operacao',
            )
        return user

    return _dep


CurrentUser = Annotated[Usuario, Depends(get_current_user)]
Admin = Annotated[Usuario, Depends(require_roles())]
Atendimento = Annotated[Usuario, Depends(require_roles('atendente'))]
Cozinha = Annotated[Usuario, Depends(require_roles('cozinha', 'atendente'))]
Financeiro = Annotated[Usuario, Depends(require_roles('financeiro'))]
Caixa = Annotated[Usuario, Depends(require_roles('atendente', 'financeiro'))]
