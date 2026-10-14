import uuid

from app.core.pix import crc16_ccitt
from tests.conftest import criar_usuario


def _chave():
    return uuid.uuid4().hex


def _conta_com_dois_pedidos(client, loja):
    h = loja['h']
    mesa_id = loja['mesa']['id']
    p1 = client.post(
        '/pedidos/',
        json={
            'id_mesa': mesa_id,
            'itens': [{'id_menu': loja['x']['id'], 'quantidade': 2}],
        },
        headers=h,
    ).json()
    client.post(
        '/pedidos/',
        json={
            'id_mesa': mesa_id,
            'itens': [{'id_menu': loja['suco']['id'], 'quantidade': 3}],
        },
        headers=h,
    )
    return p1['id_sessao'], p1


def _pagar(client, h, sid, valor, metodo='dinheiro', chave=None):
    return client.post(
        f'/contas/{sid}/pagamentos',
        json={
            'valor': valor,
            'metodo': metodo,
            'chave_idempotencia': chave or _chave(),
        },
        headers=h,
    )


def _entregar_tudo(client, h, sid):
    for p in client.get(f'/contas/{sid}', headers=h).json()['pedidos']:
        if p['status'] in {'recebido', 'em_preparo'}:
            client.patch(
                f'/pedidos/{p["id"]}/status',
                json={'status': 'pronto'},
                headers=h,
            )
        client.patch(
            f'/pedidos/{p["id"]}/status',
            json={'status': 'entregue'},
            headers=h,
        )


def test_conta_soma_varios_pedidos(client, loja):
    sid, _ = _conta_com_dois_pedidos(client, loja)
    conta = client.get(f'/contas/{sid}', headers=loja['h']).json()
    assert len(conta['pedidos']) == 2
    assert conta['resumo'] == {
        'subtotal': '75.00',
        'desconto': '0.00',
        'acrescimo': '0.00',
        'total': '75.00',
        'total_pago': '0.00',
        'saldo': '75.00',
    }


def test_desconto_acrescimo_e_permissao(client, loja):
    h = loja['h']
    sid, _ = _conta_com_dois_pedidos(client, loja)
    atendente = criar_usuario(client, h, 'atendente')
    r = client.patch(
        f'/contas/{sid}/ajustes',
        json={'desconto': '5', 'motivo_desconto': 'x'},
        headers=atendente,
    )
    assert r.status_code == 403
    r = client.patch(
        f'/contas/{sid}/ajustes', json={'desconto': '5'}, headers=h
    )
    assert r.status_code == 422
    r = client.patch(
        f'/contas/{sid}/ajustes',
        json={
            'desconto': '5.00',
            'motivo_desconto': 'Cliente fiel',
            'acrescimo': '7.50',
        },
        headers=h,
    )
    assert r.json()['resumo']['total'] == '77.50'
    r = client.patch(
        f'/contas/{sid}/ajustes',
        json={'desconto': '500', 'motivo_desconto': 'x'},
        headers=h,
    )
    assert r.status_code == 422


def test_taxa_de_servico(client, loja):
    h = loja['h']
    client.patch(
        f'/estabelecimentos/{loja["est"]["id"]}',
        json={'taxa_servico_percentual': '10'},
        headers=h,
    )
    sid, _ = _conta_com_dois_pedidos(client, loja)
    r = client.patch(
        f'/contas/{sid}/ajustes',
        json={'aplicar_taxa_servico': True},
        headers=h,
    ).json()
    assert r['resumo']['acrescimo'] == '7.50'
    assert r['resumo']['total'] == '82.50'


def test_pagamentos_parciais_e_encerramento(client, loja):
    h = loja['h']
    sid, _ = _conta_com_dois_pedidos(client, loja)
    assert _pagar(client, h, sid, '30.00').status_code == 201
    r = _pagar(client, h, sid, '100.00', 'cartao_credito')
    assert r.status_code == 422  # maior que o saldo
    assert _pagar(client, h, sid, '20.00', 'pix').status_code == 201

    conta = client.get(f'/contas/{sid}', headers=h).json()
    assert conta['resumo']['total_pago'] == '50.00'
    assert conta['resumo']['saldo'] == '25.00'

    # Nao encerra com saldo nem com pedidos em andamento
    assert client.post(f'/contas/{sid}/encerrar', headers=h).status_code == 422
    _pagar(client, h, sid, '25.00', 'cartao_debito')
    r = client.post(f'/contas/{sid}/encerrar', headers=h)
    assert r.status_code == 422 and 'pedidos' in r.json()['detail']
    _entregar_tudo(client, h, sid)
    r = client.post(f'/contas/{sid}/encerrar', headers=h)
    assert r.status_code == 200 and r.json()['status'] == 'encerrada'
    assert _pagar(client, h, sid, '1.00').status_code == 422

    mesa = client.get('/mesas/', headers=h).json()[0]
    assert mesa['situacao'] == 'livre'
    hist = client.get(
        f'/mesas/{loja["mesa"]["id"]}/historico', headers=h
    ).json()
    assert hist[0]['id'] == sid


def test_pagamento_duplicado_e_idempotente(client, loja, session_factory):
    h = loja['h']
    sid, _ = _conta_com_dois_pedidos(client, loja)
    chave = _chave()
    r1 = _pagar(client, h, sid, '10.00', chave=chave)
    r2 = _pagar(client, h, sid, '10.00', chave=chave)
    assert r1.status_code == 201 and r2.status_code == 200
    assert r1.json()['id'] == r2.json()['id']
    conta = client.get(f'/contas/{sid}', headers=h).json()
    assert len(conta['pagamentos']) == 1
    assert conta['resumo']['total_pago'] == '10.00'
    movs = client.get('/financeiro/movimentacoes', headers=h).json()
    assert len(movs) == 1 and movs[0]['valor'] == '10.00'


def test_estorno_cancela_receita(client, loja):
    h = loja['h']
    sid, _ = _conta_com_dois_pedidos(client, loja)
    pag = _pagar(client, h, sid, '10.00').json()
    r = client.post(
        f'/contas/pagamentos/{pag["id"]}/estornar',
        json={'motivo': 'erro de digitacao'},
        headers=h,
    )
    assert r.json()['status'] == 'estornado'
    conta = client.get(f'/contas/{sid}', headers=h).json()
    assert conta['resumo']['saldo'] == '75.00'
    mov = client.get('/financeiro/movimentacoes', headers=h).json()[0]
    assert mov['status'] == 'cancelada'  # mantido com historico
    assert (
        client.post(
            f'/contas/pagamentos/{pag["id"]}/estornar',
            json={'motivo': 'de novo'},
            headers=h,
        ).status_code
        == 422
    )


def test_conta_com_pedido_novo_volta_a_aberta(client, loja):
    h = loja['h']
    sid, _ = _conta_com_dois_pedidos(client, loja)
    r = client.post(f'/contas/{sid}/solicitar-fechamento', headers=h).json()
    assert r['status'] == 'aguardando_pagamento'
    assert (
        client.get('/mesas/', headers=h).json()[0]['situacao']
        == 'aguardando_pagamento'
    )
    client.post(
        '/pedidos/',
        json={
            'id_mesa': loja['mesa']['id'],
            'itens': [{'id_menu': loja['x']['id'], 'quantidade': 1}],
        },
        headers=h,
    )
    assert client.get(f'/contas/{sid}', headers=h).json()['status'] == 'aberta'


def test_abrir_conta_mesa_ocupada(client, loja):
    h = loja['h']
    _conta_com_dois_pedidos(client, loja)
    r = client.post(
        '/contas/', json={'id_mesa': loja['mesa']['id']}, headers=h
    )
    assert r.status_code == 409


def test_cobranca_pix_estatica(client, loja):
    h = loja['h']
    sid, _ = _conta_com_dois_pedidos(client, loja)
    r = client.post(f'/contas/{sid}/pix', json={}, headers=h)
    assert r.status_code == 201
    pix = r.json()
    assert pix['valor'] == '75.00'
    assert pix['status'] == 'pendente'
    assert pix['confirmacao_automatica'] is False
    code = pix['copia_e_cola']
    assert code.startswith('000201') and '540575.00' in code
    assert code[-4:] == crc16_ccitt(code[:-4])
    # Gerar a cobranca nao quita nada
    conta = client.get(f'/contas/{sid}', headers=h).json()
    assert conta['resumo']['saldo'] == '75.00'
    # Registro manual vincula a cobranca
    _pagar(client, h, sid, '75.00', 'pix')
    assert (
        client.get(f'/contas/{sid}/pix', headers=h).json()[0]['status']
        == 'paga'
    )


def test_crc16_referencia():
    # Valor de referencia do CRC-16/CCITT-FALSE
    assert crc16_ccitt('123456789') == '29B1'
