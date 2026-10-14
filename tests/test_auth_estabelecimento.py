from sqlalchemy import select

from app.models.models import Usuario
from tests.conftest import criar_usuario, registrar


def test_cadastro_nao_expoe_senha_e_grava_hash(client, session_factory):
    est, _ = registrar(client, email='dono@loja.com')
    assert 'password' not in est and 'password_hash' not in est
    with session_factory() as db:
        user = db.scalar(
            select(Usuario).where(Usuario.email == 'dono@loja.com')
        )
        assert user.perfil == 'admin'
        assert user.password_hash != 'senha1234'
        assert user.password_hash.startswith('$2')


def test_email_duplicado_no_cadastro(client):
    registrar(client, email='a@a.com')
    r = client.post(
        '/estabelecimentos/',
        json={
            'nome_loja': 'Outra',
            'chave_pix': 'x',
            'nome_titular': 'y',
            'email': 'A@a.com',
            'password': 'senha1234',
        },
    )
    assert r.status_code == 409


def test_login_invalido_e_rotas_protegidas(client):
    registrar(client, email='b@b.com')
    r = client.post('/auth/login', json={'email': 'b@b.com', 'password': 'x'})
    assert r.status_code == 401
    assert client.get('/categorias/').status_code == 401
    r = client.get(
        '/categorias/', headers={'Authorization': 'Bearer token-falso'}
    )
    assert r.status_code == 401


def test_login_oauth2_form(client):
    registrar(client, email='c@c.com')
    r = client.post(
        '/auth/token', data={'username': 'c@c.com', 'password': 'senha1234'}
    )
    assert r.status_code == 200
    assert r.json()['token_type'] == 'bearer'


def test_permissoes_por_perfil(client):
    _, admin = registrar(client)
    cozinha = criar_usuario(client, admin, 'cozinha')
    financeiro = criar_usuario(client, admin, 'financeiro')
    atendente = criar_usuario(client, admin, 'atendente')

    assert client.get('/pedidos/', headers=cozinha).status_code == 200
    assert (
        client.get('/financeiro/movimentacoes', headers=cozinha).status_code
        == 403
    )
    assert (
        client.post(
            '/categorias/', json={'nome': 'X'}, headers=cozinha
        ).status_code
        == 403
    )
    assert (
        client.get('/financeiro/movimentacoes', headers=financeiro).status_code
        == 200
    )
    assert client.get('/mesas/', headers=financeiro).status_code == 403
    assert client.get('/mesas/', headers=atendente).status_code == 200
    assert client.get('/usuarios/', headers=atendente).status_code == 403
    assert client.get('/usuarios/', headers=admin).status_code == 200


def test_patch_estabelecimento_conflito_de_email(client):
    est1, h1 = registrar(client, email='um@x.com')
    registrar(client, email='dois@x.com')
    r = client.patch(
        f'/estabelecimentos/{est1["id"]}',
        json={'email': 'dois@x.com'},
        headers=h1,
    )
    assert r.status_code == 409
    r = client.patch(
        f'/estabelecimentos/{est1["id"]}',
        json={'nome_loja': 'Novo nome', 'taxa_servico_percentual': '10'},
        headers=h1,
    )
    assert r.status_code == 200
    assert r.json()['nome_loja'] == 'Novo nome'


def test_nao_acessa_outro_estabelecimento(client):
    _, h1 = registrar(client)
    est2, _ = registrar(client)
    r = client.patch(
        f'/estabelecimentos/{est2["id"]}',
        json={'nome_loja': 'hack'},
        headers=h1,
    )
    assert r.status_code == 404


def test_troca_de_senha_usa_hash(client, session_factory):
    _, admin = registrar(client)
    r = client.get('/usuarios/', headers=admin)
    uid = r.json()[0]['id']
    r = client.patch(
        f'/usuarios/{uid}', json={'password': 'novasenha99'}, headers=admin
    )
    assert r.status_code == 200
    with session_factory() as db:
        assert db.get(Usuario, uid).password_hash != 'novasenha99'
    email = r.json()['email']
    r = client.post(
        '/auth/login', json={'email': email, 'password': 'novasenha99'}
    )
    assert r.status_code == 200


def test_ultimo_admin_nao_pode_ser_rebaixado(client):
    _, admin = registrar(client)
    uid = client.get('/usuarios/', headers=admin).json()[0]['id']
    r = client.patch(
        f'/usuarios/{uid}', json={'perfil': 'cozinha'}, headers=admin
    )
    assert r.status_code == 422
