def test_cardapio_publico(client, loja):
    slug = loja['est']['slug']
    r = client.get(f'/public/{slug}')
    assert r.status_code == 200
    body = r.json()
    assert body['estabelecimento'] == {
        'nome_loja': 'Lanchonete Teste',
        'slug': slug,
    }
    assert body['mesa_numero'] is None
    assert {p['nome'] for p in body['categorias'][0]['produtos']} == {
        'X-Burger',
        'Suco',
    }

    r = client.get(f'/public/{slug}', params={'mesa': loja['mesa']['token']})
    assert r.json()['mesa_numero'] == '1'
    assert (
        client.get(f'/public/{slug}', params={'mesa': 'invalido'}).status_code
        == 404
    )
    assert client.get('/public/nao-existe').status_code == 404


def test_produto_desativado_some_do_cardapio(client, loja):
    client.patch(
        f'/menu/{loja["suco"]["id"]}', json={'ativo': False}, headers=loja['h']
    )
    body = client.get(f'/public/{loja["est"]["slug"]}').json()
    assert [p['nome'] for p in body['categorias'][0]['produtos']] == [
        'X-Burger'
    ]


def test_pedido_publico_pela_mesa_e_acompanhamento(client, loja):
    slug = loja['est']['slug']
    body = {
        'mesa_token': loja['mesa']['token'],
        'itens': [{'id_menu': loja['x']['id'], 'quantidade': 1}],
    }
    r1 = client.post(f'/public/{slug}/pedidos', json=body)
    r2 = client.post(f'/public/{slug}/pedidos', json=body)
    assert r1.status_code == 201
    codigo = r1.json()['codigo_acompanhamento']

    pedidos = client.get('/pedidos/', headers=loja['h']).json()
    assert len({p['id_sessao'] for p in pedidos}) == 1
    assert {p['origem'] for p in pedidos} == {'cliente'}

    pub = client.get(f'/public/pedidos/{codigo}').json()
    assert pub['status'] == 'recebido'
    assert pub['mesa_numero'] == '1'
    assert pub['numero'] == r1.json()['numero']
    # Sem dados internos ou pessoais
    for campo in (
        'cliente_nome',
        'id_sessao',
        'codigo_acompanhamento',
        'observacao',
    ):
        assert campo not in pub
    assert r2.json()['codigo_acompanhamento'] != codigo
    assert client.get('/public/pedidos/codigo-inexistente').status_code == 404


def test_pedido_publico_nao_aceita_preco_do_cliente(client, loja):
    slug = loja['est']['slug']
    r = client.post(
        f'/public/{slug}/pedidos',
        json={
            'tipo': 'retirada',
            'cliente_nome': 'Ana',
            'itens': [
                {'id_menu': loja['x']['id'], 'quantidade': 1, 'preco': '0.01'}
            ],
            'total': '0.01',
        },
    )
    assert r.status_code == 201
    pedidos = client.get('/pedidos/', headers=loja['h']).json()
    assert pedidos[0]['total'] == '25.50'


def test_pedido_publico_mesa_sem_token(client, loja):
    r = client.post(
        f'/public/{loja["est"]["slug"]}/pedidos',
        json={
            'tipo': 'mesa',
            'itens': [{'id_menu': loja['x']['id'], 'quantidade': 1}],
        },
    )
    assert r.status_code == 422


def test_qrcodes(client, loja):
    h = loja['h']
    r = client.get(f'/mesas/{loja["mesa"]["id"]}/qrcode', headers=h).json()
    assert r['url'].endswith(
        f'/c/{loja["est"]["slug"]}?mesa={loja["mesa"]["token"]}'
    )
    geral = client.get('/estabelecimentos/me/qrcode', headers=h).json()
    assert geral['url'].endswith(f'/c/{loja["est"]["slug"]}')

    nova = client.post(
        f'/mesas/{loja["mesa"]["id"]}/regenerar-token', headers=h
    ).json()
    assert nova['token'] != loja['mesa']['token']
    r = client.get(
        f'/public/{loja["est"]["slug"]}',
        params={'mesa': loja['mesa']['token']},
    )
    assert r.status_code == 404
