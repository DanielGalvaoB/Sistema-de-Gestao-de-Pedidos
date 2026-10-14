from datetime import timedelta

from sqlalchemy import func, select

from app.models.models import Pedido
from tests.conftest import criar_usuario


def _pedido(client, loja, itens, **extra):
    body = {'itens': itens, **extra}
    if (
        'id_mesa' not in extra
        and 'tipo' not in extra
        and 'id_sessao' not in extra
    ):
        body['id_mesa'] = loja['mesa']['id']
    return client.post('/pedidos/', json=body, headers=loja['h'])


def test_pedido_valido_usa_preco_do_banco(client, loja):
    r = _pedido(
        client,
        loja,
        [
            {
                'id_menu': loja['x']['id'],
                'quantidade': 2,
                'observacao': 'sem cebola',
            },
            {'id_menu': loja['suco']['id'], 'quantidade': 1},
        ],
    )
    assert r.status_code == 201, r.text
    p = r.json()
    assert p['total'] == '59.00'
    assert p['status'] == 'recebido'
    assert p['mesa_numero'] == '1'
    assert p['itens'][0]['observacao'] == 'sem cebola'
    assert p['previsao_pronto'] is not None


def test_pedido_invalido_nao_persiste_nada(client, loja, session_factory):
    casos = [
        [{'id_menu': 9999, 'quantidade': 1}],
        [{'id_menu': loja['x']['id'], 'quantidade': 0}],
        [{'id_menu': loja['x']['id'], 'quantidade': -1}],
        [],
        [
            {'id_menu': loja['x']['id'], 'quantidade': 1},
            {'id_menu': 9999, 'quantidade': 1},
        ],
    ]
    for itens in casos:
        r = _pedido(client, loja, itens)
        assert r.status_code == 422, itens
    with session_factory() as db:
        assert db.scalar(select(func.count(Pedido.id))) == 0


def test_produto_indisponivel_rejeitado(client, loja):
    client.patch(
        f'/menu/{loja["x"]["id"]}',
        json={'is_disponivel': False},
        headers=loja['h'],
    )
    r = _pedido(client, loja, [{'id_menu': loja['x']['id'], 'quantidade': 1}])
    assert r.status_code == 422
    assert 'indisponivel' in r.json()['detail']


def test_produto_de_outro_estabelecimento_rejeitado(client, loja):
    from tests.conftest import registrar

    _, outro = registrar(client)
    r = client.post(
        '/pedidos/',
        json={
            'tipo': 'balcao',
            'itens': [{'id_menu': loja['x']['id'], 'quantidade': 1}],
        },
        headers=outro,
    )
    assert r.status_code == 422


def test_fluxo_de_status_do_pedido(client, loja):
    h = loja['h']
    p = _pedido(
        client, loja, [{'id_menu': loja['x']['id'], 'quantidade': 1}]
    ).json()
    url = f'/pedidos/{p["id"]}/status'
    assert (
        client.patch(url, json={'status': 'entregue'}, headers=h).status_code
        == 422
    )
    r = client.patch(url, json={'status': 'em_preparo'}, headers=h)
    assert r.json()['status'] == 'em_preparo' and r.json()['iniciado_em']
    r = client.patch(url, json={'status': 'pronto'}, headers=h)
    assert r.json()['status'] == 'pronto'
    assert all(i['status'] == 'pronto' for i in r.json()['itens'])
    r = client.patch(url, json={'status': 'entregue'}, headers=h)
    assert r.json()['status'] == 'entregue' and r.json()['entregue_em']
    assert (
        client.patch(
            url, json={'status': 'cancelado', 'motivo': 'x'}, headers=h
        ).status_code
        == 422
    )

    det = client.get(f'/pedidos/{p["id"]}', headers=h).json()
    assert [
        x['status_novo'] for x in det['historico'] if x['id_item'] is None
    ] == [
        'recebido',
        'em_preparo',
        'pronto',
        'entregue',
    ]


def test_status_por_item_nao_marca_pedido_pronto_com_itens_pendentes(
    client, loja
):
    h = loja['h']
    p = _pedido(
        client,
        loja,
        [
            {'id_menu': loja['x']['id'], 'quantidade': 1},
            {'id_menu': loja['suco']['id'], 'quantidade': 1},
        ],
    ).json()
    i1, i2 = (i['id'] for i in p['itens'])
    base = f'/pedidos/{p["id"]}/itens'

    r = client.patch(
        f'{base}/{i2}/status', json={'status': 'pronto'}, headers=h
    )
    assert r.json()['status'] == 'em_preparo'
    assert (
        client.patch(
            f'/pedidos/{p["id"]}/status',
            json={'status': 'entregue'},
            headers=h,
        ).status_code
        == 422
    )

    r = client.patch(
        f'{base}/{i1}/status', json={'status': 'em_preparo'}, headers=h
    )
    assert r.json()['status'] == 'em_preparo'
    r = client.patch(
        f'{base}/{i1}/status', json={'status': 'pronto'}, headers=h
    )
    assert r.json()['status'] == 'pronto'
    assert r.json()['pronto_em'] is not None


def test_cancelar_item_e_pedido(client, loja):
    h = loja['h']
    p = _pedido(
        client,
        loja,
        [
            {'id_menu': loja['x']['id'], 'quantidade': 1},
            {'id_menu': loja['suco']['id'], 'quantidade': 1},
        ],
    ).json()
    i1 = p['itens'][0]['id']
    r = client.patch(
        f'/pedidos/{p["id"]}/itens/{i1}/status',
        json={'status': 'cancelado'},
        headers=h,
    )
    assert r.json()['total'] == '8.00'

    url = f'/pedidos/{p["id"]}/status'
    assert (
        client.patch(url, json={'status': 'cancelado'}, headers=h).status_code
        == 422
    )
    r = client.patch(
        url,
        json={'status': 'cancelado', 'motivo': 'cliente desistiu'},
        headers=h,
    )
    assert r.json()['status'] == 'cancelado'
    assert r.json()['motivo_cancelamento'] == 'cliente desistiu'
    assert r.json()['total'] == '0.00'


def test_atraso_e_nova_previsao(client, loja, session_factory):
    h = loja['h']
    p = _pedido(
        client, loja, [{'id_menu': loja['x']['id'], 'quantidade': 1}]
    ).json()
    with session_factory() as db:
        pedido = db.get(Pedido, p['id'])
        pedido.created_at -= timedelta(minutes=40)
        pedido.previsao_pronto -= timedelta(minutes=40)
        db.commit()
    r = client.get('/pedidos/', params={'ativos': True}, headers=h).json()[0]
    assert r['atrasado'] is True and r['minutos_atraso'] >= 19
    assert r['itens'][0]['atrasado'] is True

    r = client.patch(
        f'/pedidos/{p["id"]}/previsao',
        json={'minutos_adicionais': 10, 'motivo_atraso': 'Forno cheio'},
        headers=h,
    ).json()
    assert r['atrasado'] is False
    assert r['motivo_atraso'] == 'Forno cheio'

    pub = client.get(f'/public/pedidos/{p["codigo_acompanhamento"]}').json()
    assert pub['motivo_atraso'] == 'Forno cheio'
    assert pub['previsao_pronto'] is not None


def test_pedidos_de_mesas_diferentes_nao_se_misturam(client, loja):
    h = loja['h']
    mesa2 = client.post('/mesas/', json={'numero': '2'}, headers=h).json()
    a = _pedido(
        client, loja, [{'id_menu': loja['x']['id'], 'quantidade': 1}]
    ).json()
    b = _pedido(
        client,
        loja,
        [{'id_menu': loja['suco']['id'], 'quantidade': 1}],
        id_mesa=mesa2['id'],
    ).json()
    c = _pedido(
        client, loja, [{'id_menu': loja['suco']['id'], 'quantidade': 2}]
    ).json()
    assert a['id_sessao'] == c['id_sessao'] != b['id_sessao']

    mesas = {m['numero']: m for m in client.get('/mesas/', headers=h).json()}
    assert mesas['1']['situacao'] == 'ocupada'
    assert mesas['1']['total_consumido'] == '41.50'
    assert mesas['2']['total_consumido'] == '8.00'


def test_pedido_balcao_cria_conta_propria(client, loja):
    a = _pedido(
        client,
        loja,
        [{'id_menu': loja['x']['id'], 'quantidade': 1}],
        tipo='balcao',
    ).json()
    b = _pedido(
        client,
        loja,
        [{'id_menu': loja['x']['id'], 'quantidade': 1}],
        tipo='retirada',
    ).json()
    assert a['id_sessao'] != b['id_sessao']
    assert a['mesa_numero'] is None and b['tipo_atendimento'] == 'retirada'


def test_cozinha_altera_status_mas_nao_cria_pedido(client, loja):
    cozinha = criar_usuario(client, loja['h'], 'cozinha')
    p = _pedido(
        client, loja, [{'id_menu': loja['x']['id'], 'quantidade': 1}]
    ).json()
    r = client.patch(
        f'/pedidos/{p["id"]}/status',
        json={'status': 'em_preparo'},
        headers=cozinha,
    )
    assert r.status_code == 200
    r = client.post(
        '/pedidos/',
        json={
            'tipo': 'balcao',
            'itens': [{'id_menu': loja['x']['id'], 'quantidade': 1}],
        },
        headers=cozinha,
    )
    assert r.status_code == 403


def test_websocket_avisa_mudancas(client, loja):
    token = loja['h']['Authorization'].split()[1]
    with client.websocket_connect(f'/ws/pedidos?token={token}') as ws:
        assert ws.receive_json()['evento'] == 'conectado'
        _pedido(client, loja, [{'id_menu': loja['x']['id'], 'quantidade': 1}])
        assert ws.receive_json()['evento'] == 'atualizar'


def test_websocket_rejeita_token_invalido(client):
    import pytest
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect('/ws/pedidos?token=invalido') as ws:
            ws.receive_json()
