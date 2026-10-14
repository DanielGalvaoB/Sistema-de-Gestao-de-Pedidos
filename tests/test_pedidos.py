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
    # Sem previsao automatica: so existe quando o estabelecimento informa
    assert p['previsao_pronto'] is None
    assert p['atrasado'] is False and p['alerta_prazo'] is False


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


def test_previsao_so_quando_informada(client, loja, session_factory):
    h = loja['h']
    p = _pedido(
        client, loja, [{'id_menu': loja['x']['id'], 'quantidade': 1}]
    ).json()
    # Mesmo antigo, pedido sem previsao informada nunca fica atrasado
    with session_factory() as db:
        db.get(Pedido, p['id']).created_at -= timedelta(hours=2)
        db.commit()
    r = client.get('/pedidos/', params={'ativos': True}, headers=h).json()[0]
    assert r['atrasado'] is False and r['previsao_pronto'] is None
    pub = client.get(f'/public/pedidos/{p["codigo_acompanhamento"]}').json()
    assert pub['previsao_pronto'] is None

    # Estabelecimento informa um imprevisto: +3 min -> alerta (faltam <= 5)
    r = client.patch(
        f'/pedidos/{p["id"]}/previsao',
        json={'minutos_adicionais': 3, 'motivo_atraso': 'Falta de gas'},
        headers=h,
    ).json()
    assert r['previsao_pronto'] is not None
    assert r['atrasado'] is False and r['alerta_prazo'] is True

    # Prazo informado vencido -> atrasado, com o item pendente marcado
    with session_factory() as db:
        db.get(Pedido, p['id']).previsao_pronto -= timedelta(minutes=25)
        db.commit()
    r = client.get('/pedidos/', params={'ativos': True}, headers=h).json()[0]
    assert r['atrasado'] is True and r['minutos_atraso'] >= 20
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


def _pagar_pedido(client, h, pid, metodo='dinheiro', valor=None, chave=None):
    import uuid

    body = {'metodo': metodo, 'chave_idempotencia': chave or uuid.uuid4().hex}
    if valor is not None:
        body['valor'] = valor
    return client.post(f'/pedidos/{pid}/pagamentos', json=body, headers=h)


def test_confirmar_pagamento_do_pedido_pronto(client, loja):
    h = loja['h']
    p = _pedido(
        client, loja, [{'id_menu': loja['x']['id'], 'quantidade': 2}]
    ).json()
    assert p['pago'] is False and p['saldo'] == '51.00'

    # Antes de ficar pronto nao confirma
    assert _pagar_pedido(client, h, p['id']).status_code == 422
    client.patch(
        f'/pedidos/{p["id"]}/status', json={'status': 'pronto'}, headers=h
    )

    # Metodo obrigatorio e validado
    r = client.post(
        f'/pedidos/{p["id"]}/pagamentos',
        json={'chave_idempotencia': 'x' * 10},
        headers=h,
    )
    assert r.status_code == 422
    r = _pagar_pedido(client, h, p['id'], metodo='cheque')
    assert r.status_code == 422

    r = _pagar_pedido(client, h, p['id'], 'cartao_debito', valor='20.00')
    assert r.status_code == 201
    assert r.json()['total_pago'] == '20.00' and r.json()['pago'] is False
    assert _pagar_pedido(client, h, p['id'], valor='40.00').status_code == 422

    chave = 'chave-final-123'
    r = _pagar_pedido(client, h, p['id'], 'pix', chave=chave)
    assert r.status_code == 201 and r.json()['pago'] is True
    assert (
        _pagar_pedido(client, h, p['id'], 'pix', chave=chave).status_code
        == 200
    )
    assert _pagar_pedido(client, h, p['id']).status_code == 422  # ja pago

    conta = client.get(f'/contas/{p["id_sessao"]}', headers=h).json()
    assert [
        (x['metodo'], x['valor'], x['id_pedido']) for x in conta['pagamentos']
    ] == [
        ('cartao_debito', '20.00', p['id']),
        ('pix', '31.00', p['id']),
    ]
    assert conta['resumo']['saldo'] == '0.00'
    movs = client.get('/financeiro/movimentacoes', headers=h).json()
    assert len(movs) == 2 and all(m['automatica'] for m in movs)


def test_pagamento_de_um_pedido_nao_quita_outro_da_mesma_mesa(client, loja):
    h = loja['h']
    a = _pedido(
        client, loja, [{'id_menu': loja['x']['id'], 'quantidade': 1}]
    ).json()
    b = _pedido(
        client, loja, [{'id_menu': loja['suco']['id'], 'quantidade': 1}]
    ).json()
    for p in (a, b):
        client.patch(
            f'/pedidos/{p["id"]}/status', json={'status': 'pronto'}, headers=h
        )
    r = _pagar_pedido(client, h, a['id'], 'cartao_credito')
    assert r.json()['pago'] is True
    outro = client.get(f'/pedidos/{b["id"]}', headers=h).json()
    assert outro['pago'] is False and outro['saldo'] == '8.00'
    conta = client.get(f'/contas/{a["id_sessao"]}', headers=h).json()
    assert conta['resumo']['saldo'] == '8.00'


def test_cozinha_nao_confirma_pagamento(client, loja):
    cozinha = criar_usuario(client, loja['h'], 'cozinha')
    p = _pedido(
        client, loja, [{'id_menu': loja['x']['id'], 'quantidade': 1}]
    ).json()
    client.patch(
        f'/pedidos/{p["id"]}/status',
        json={'status': 'pronto'},
        headers=loja['h'],
    )
    assert _pagar_pedido(client, cozinha, p['id']).status_code == 403


def test_pagamento_da_conta_inteira_quita_os_pedidos(client, loja):
    import uuid

    h = loja['h']
    p = _pedido(
        client, loja, [{'id_menu': loja['x']['id'], 'quantidade': 1}]
    ).json()
    client.patch(
        f'/pedidos/{p["id"]}/status', json={'status': 'pronto'}, headers=h
    )
    client.post(
        f'/contas/{p["id_sessao"]}/pagamentos',
        json={
            'valor': '25.50',
            'metodo': 'dinheiro',
            'chave_idempotencia': uuid.uuid4().hex,
        },
        headers=h,
    )
    r = client.get(f'/pedidos/{p["id"]}', headers=h).json()
    assert r['pago'] is True and r['saldo'] == '0.00'
    assert _pagar_pedido(client, h, p['id']).status_code == 422
