from tests.conftest import registrar


def test_get_categoria_inexistente_retorna_404(client):
    _, h = registrar(client)
    assert client.get('/categorias/999', headers=h).status_code == 404


def test_crud_categoria(client):
    _, h = registrar(client)
    r = client.post('/categorias/', json={'nome': 'Bebidas'}, headers=h)
    assert r.status_code == 201
    cid = r.json()['id']
    assert (
        client.get(f'/categorias/{cid}', headers=h).json()['nome'] == 'Bebidas'
    )
    assert (
        client.post(
            '/categorias/', json={'nome': 'bebidas'}, headers=h
        ).status_code
        == 409
    )

    r = client.patch(f'/categorias/{cid}', json={'ordem': 3}, headers=h)
    assert r.json() == {
        'id': cid,
        'nome': 'Bebidas',
        'ordem': 3,
        'ativo': True,
    }

    assert client.delete(f'/categorias/{cid}', headers=h).status_code == 204
    assert client.get(f'/categorias/{cid}', headers=h).status_code == 404


def test_put_categoria_exige_nome(client):
    _, h = registrar(client)
    cid = client.post('/categorias/', json={'nome': 'A'}, headers=h).json()[
        'id'
    ]
    assert (
        client.put(f'/categorias/{cid}', json={}, headers=h).status_code == 422
    )
    r = client.put(f'/categorias/{cid}', json={'nome': None}, headers=h)
    assert r.status_code == 422
    r = client.patch(f'/categorias/{cid}', json={'nome': None}, headers=h)
    assert r.status_code == 200
    assert r.json()['nome'] == 'A'
    r = client.put(f'/categorias/{cid}', json={'nome': 'B'}, headers=h)
    assert r.status_code == 200 and r.json()['nome'] == 'B'


def test_categoria_com_produto_nao_e_excluida(client, loja):
    r = client.delete(f'/categorias/{loja["cat_id"]}', headers=loja['h'])
    assert r.status_code == 409


def test_menu_vazio_retorna_lista(client):
    _, h = registrar(client)
    r = client.get('/menu/', headers=h)
    assert r.status_code == 200
    assert r.json() == []


def test_produto_validacoes(client, loja):
    h = loja['h']
    r = client.post(
        '/menu/',
        json={'nome': 'X', 'preco': '-1', 'id_categoria': loja['cat_id']},
        headers=h,
    )
    assert r.status_code == 422
    r = client.post(
        '/menu/',
        json={'nome': 'X', 'preco': '1', 'id_categoria': 999},
        headers=h,
    )
    assert r.status_code == 422
    r = client.patch(
        f'/menu/{loja["x"]["id"]}', json={'preco': None}, headers=h
    )
    assert r.status_code == 422


def test_isolamento_entre_estabelecimentos(client, loja):
    _, outro = registrar(client)
    assert (
        client.get(f'/menu/{loja["x"]["id"]}', headers=outro).status_code
        == 404
    )
    assert (
        client.get(f'/categorias/{loja["cat_id"]}', headers=outro).status_code
        == 404
    )
    assert client.get('/menu/', headers=outro).json() == []


def test_busca_e_filtros(client, loja):
    h = loja['h']
    r = client.get('/menu/', params={'busca': 'burg'}, headers=h)
    assert [p['nome'] for p in r.json()] == ['X-Burger']
    client.patch(
        f'/menu/{loja["suco"]["id"]}', json={'is_disponivel': False}, headers=h
    )
    r = client.get('/menu/', params={'disponivel': True}, headers=h)
    assert [p['nome'] for p in r.json()] == ['X-Burger']


def test_alteracao_de_preco_registra_historico_e_nao_altera_pedidos(
    client, loja
):
    h = loja['h']
    pid = loja['x']['id']
    pedido = client.post(
        '/pedidos/',
        json={
            'id_mesa': loja['mesa']['id'],
            'itens': [{'id_menu': pid, 'quantidade': 2}],
        },
        headers=h,
    ).json()
    client.patch(f'/menu/{pid}', json={'preco': '30.00'}, headers=h)

    hist = client.get(f'/menu/{pid}/historico-precos', headers=h).json()
    assert (
        hist[0]['preco_anterior'] == '25.50'
        and hist[0]['preco_novo'] == '30.00'
    )

    p2 = client.get(f'/pedidos/{pedido["id"]}', headers=h).json()
    assert p2['itens'][0]['preco_unitario'] == '25.50'
    assert p2['total'] == '51.00'


def test_excluir_produto_vendido_apenas_desativa(client, loja):
    h = loja['h']
    pid = loja['x']['id']
    client.post(
        '/pedidos/',
        json={'tipo': 'balcao', 'itens': [{'id_menu': pid, 'quantidade': 1}]},
        headers=h,
    )
    r = client.delete(f'/menu/{pid}', headers=h)
    assert r.status_code == 204 and r.headers['X-Resultado'] == 'desativado'
    assert client.get(f'/menu/{pid}', headers=h).json()['ativo'] is False
    r = client.delete(f'/menu/{loja["suco"]["id"]}', headers=h)
    assert r.headers['X-Resultado'] == 'excluido'
