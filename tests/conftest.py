import os
import tempfile  # noqa: E402
import uuid

os.environ.setdefault('BCRYPT_ROUNDS', '4')
os.environ.setdefault('UPLOAD_DIR', tempfile.mkdtemp(prefix='pdv_uploads_'))
os.environ.setdefault('SECRET_KEY', 'chave-de-teste-com-pelo-menos-32-bytes!!')

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.app import app  # noqa: E402
from app.database import Base  # noqa: E402
from app.dependencies.db_dep import get_db  # noqa: E402


@pytest.fixture
def engine():
    eng = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture
def client(session_factory):
    def _get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def auth(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def registrar(client, nome='Lanchonete Teste', email=None, senha='senha1234'):
    email = email or f'{uuid.uuid4().hex[:8]}@teste.com'
    r = client.post(
        '/estabelecimentos/',
        json={
            'nome_loja': nome,
            'chave_pix': 'pix@teste.com',
            'nome_titular': 'Fulano de Tal',
            'email': email,
            'password': senha,
        },
    )
    assert r.status_code == 201, r.text
    tok = client.post(
        '/auth/login', json={'email': email, 'password': senha}
    ).json()['access_token']
    return r.json(), auth(tok)


def criar_usuario(client, admin_h, perfil):
    email = f'{perfil}-{uuid.uuid4().hex[:6]}@teste.com'
    r = client.post(
        '/usuarios/',
        json={
            'nome': perfil,
            'email': email,
            'password': 'senha1234',
            'perfil': perfil,
        },
        headers=admin_h,
    )
    assert r.status_code == 201, r.text
    tok = client.post(
        '/auth/login', json={'email': email, 'password': 'senha1234'}
    ).json()['access_token']
    return auth(tok)


@pytest.fixture
def loja(client):
    """Estabelecimento com uma categoria, dois produtos e uma mesa."""
    est, h = registrar(client)
    cat = client.post('/categorias/', json={'nome': 'Lanches'}, headers=h)
    cat_id = cat.json()['id']
    x = client.post(
        '/menu/',
        json={'nome': 'X-Burger', 'preco': '25.50', 'id_categoria': cat_id},
        headers=h,
    ).json()
    suco = client.post(
        '/menu/',
        json={
            'nome': 'Suco',
            'preco': '8.00',
            'id_categoria': cat_id,
        },
        headers=h,
    ).json()
    mesa = client.post('/mesas/', json={'numero': '1'}, headers=h).json()
    return {
        'est': est,
        'h': h,
        'cat_id': cat_id,
        'x': x,
        'suco': suco,
        'mesa': mesa,
    }
