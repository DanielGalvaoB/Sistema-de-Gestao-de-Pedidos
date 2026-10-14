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


def _png(tamanho=(1600, 900), cor=(200, 30, 30)):
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new('RGB', tamanho, cor).save(buf, 'PNG')
    return buf.getvalue()


def test_upload_de_imagem_do_produto(client, loja):
    import io

    from PIL import Image

    h = loja['h']
    pid = loja['x']['id']
    r = client.post(
        f'/menu/{pid}/imagem',
        files={'arquivo': ('foto.png', _png(), 'image/png')},
        headers=h,
    )
    assert r.status_code == 200, r.text
    url = r.json()['url_imagem']
    assert url.startswith('/uploads/produtos/') and url.endswith('.webp')

    servida = client.get(url)
    assert servida.status_code == 200
    assert servida.headers['content-type'] == 'image/webp'
    img = Image.open(io.BytesIO(servida.content))
    assert img.format == 'WEBP' and max(img.size) == 1200  # redimensionada

    # Aparece no cardapio publico
    body = client.get(f'/public/{loja["est"]["slug"]}').json()
    produto = next(
        p for p in body['categorias'][0]['produtos'] if p['id'] == pid
    )
    assert produto['url_imagem'] == url

    # Substituir apaga o arquivo antigo
    r2 = client.post(
        f'/menu/{pid}/imagem',
        files={'arquivo': ('nova.png', _png(cor=(0, 0, 255)), 'image/png')},
        headers=h,
    )
    assert r2.json()['url_imagem'] != url
    assert client.get(url).status_code == 404

    r3 = client.delete(f'/menu/{pid}/imagem', headers=h)
    assert r3.json()['url_imagem'] is None
    assert client.get(r2.json()['url_imagem']).status_code == 404


def test_upload_rejeita_arquivo_invalido(client, loja):
    from tests.conftest import criar_usuario, registrar

    h = loja['h']
    pid = loja['x']['id']
    r = client.post(
        f'/menu/{pid}/imagem',
        files={
            'arquivo': ('foto.png', b'<script>alert(1)</script>', 'image/png')
        },
        headers=h,
    )
    assert r.status_code == 422
    _, outro = registrar(client)
    r = client.post(
        f'/menu/{pid}/imagem',
        files={'arquivo': ('foto.png', _png(), 'image/png')},
        headers=outro,
    )
    assert r.status_code == 404
    cozinha = criar_usuario(client, h, 'cozinha')
    r = client.post(
        f'/menu/{pid}/imagem',
        files={'arquivo': ('foto.png', _png(), 'image/png')},
        headers=cozinha,
    )
    assert r.status_code == 403


def test_contas_com_pedidos_no_caixa(client, loja):
    h = loja['h']
    client.post(
        '/pedidos/',
        json={
            'tipo': 'balcao',
            'cliente_nome': 'Bia',
            'itens': [{'id_menu': loja['x']['id'], 'quantidade': 2}],
        },
        headers=h,
    )
    contas = client.get(
        '/contas/',
        params={'status': ['aberta'], 'com_pedidos': True},
        headers=h,
    ).json()
    assert len(contas) == 1
    c = contas[0]
    assert c['cliente_nome'] == 'Bia' and c['resumo']['total'] == '51.00'
    assert c['pedidos'][0]['itens'][0]['nome_produto'] == 'X-Burger'
