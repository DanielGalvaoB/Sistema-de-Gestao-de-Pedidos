import uuid
from datetime import date, timedelta

from app.core.utils import utcnow
from app.models.models import Pedido


def _cat(client, h, nome):
    cats = client.get('/financeiro/categorias', headers=h).json()
    return next(c for c in cats if c['nome'] == nome)


def _entrada(client, h, **extra):
    outras = _cat(client, h, 'Outras receitas')
    body = {
        'descricao': 'Gorjeta repassada',
        'id_categoria': outras['id'],
        'valor': '20.00',
        'metodo_pagamento': 'dinheiro',
        **extra,
    }
    return client.post('/financeiro/movimentacoes', json=body, headers=h)


def test_somente_categorias_de_entrada(client, loja):
    cats = client.get('/financeiro/categorias', headers=loja['h']).json()
    assert {c['nome'] for c in cats} == {'Vendas', 'Outras receitas'}
    assert all(c['tipo'] == 'entrada' for c in cats)


def test_saidas_nao_sao_aceitas(client, loja):
    h = loja['h']
    outras = _cat(client, h, 'Outras receitas')
    r = client.post(
        '/financeiro/movimentacoes',
        json={
            'tipo': 'saida',
            'descricao': 'Conta de luz',
            'id_categoria': outras['id'],
            'valor': '100',
        },
        headers=h,
    )
    assert r.status_code == 422
    r = client.post(
        '/financeiro/categorias',
        json={'nome': 'Aluguel', 'tipo': 'saida'},
        headers=h,
    )
    assert r.status_code == 422


def test_vendas_protegida(client, loja):
    h = loja['h']
    vendas = _cat(client, h, 'Vendas')
    assert vendas['sistema'] is True
    assert _entrada(client, h, id_categoria=vendas['id']).status_code == 422
    r = client.patch(
        f'/financeiro/categorias/{vendas["id"]}', json={'nome': 'y'}, headers=h
    )
    assert r.status_code == 422


def test_entrada_manual_editar_e_cancelar(client, loja):
    h = loja['h']
    r = _entrada(client, h)
    assert r.status_code == 201 and r.json()['tipo'] == 'entrada'
    mid = r.json()['id']
    r = client.patch(
        f'/financeiro/movimentacoes/{mid}', json={'valor': '25.00'}, headers=h
    )
    assert r.json()['valor'] == '25.00'
    r = client.post(
        f'/financeiro/movimentacoes/{mid}/cancelar',
        json={'motivo': 'lancado errado'},
        headers=h,
    )
    assert r.json()['status'] == 'cancelada'
    r = client.patch(
        f'/financeiro/movimentacoes/{mid}', json={'valor': '1'}, headers=h
    )
    assert r.status_code == 422
    todas = client.get('/financeiro/movimentacoes', headers=h).json()
    assert len(todas) == 1  # nada e apagado


def test_valor_invalido(client, loja):
    for valor in ('0', '-5', '1.234'):
        assert _entrada(client, loja['h'], valor=valor).status_code == 422


def test_lancamento_de_pagamento_nao_editavel(client, loja):
    h = loja['h']
    p = client.post(
        '/pedidos/',
        json={
            'tipo': 'balcao',
            'itens': [{'id_menu': loja['x']['id'], 'quantidade': 1}],
        },
        headers=h,
    ).json()
    client.post(
        f'/contas/{p["id_sessao"]}/pagamentos',
        json={
            'valor': '25.50',
            'metodo': 'dinheiro',
            'chave_idempotencia': uuid.uuid4().hex,
        },
        headers=h,
    )
    mov = client.get('/financeiro/movimentacoes', headers=h).json()[0]
    assert mov['automatica'] is True and mov['categoria_nome'] == 'Vendas'
    r = client.patch(
        f'/financeiro/movimentacoes/{mov["id"]}',
        json={'valor': '1'},
        headers=h,
    )
    assert r.status_code == 422
    r = client.post(
        f'/financeiro/movimentacoes/{mov["id"]}/cancelar',
        json={'motivo': 'xxx'},
        headers=h,
    )
    assert r.status_code == 422


def test_relatorio_de_vendas_e_recebimentos(client, loja, session_factory):
    h = loja['h']
    hoje = date.today()
    # Pedido 1: pago (25.50). Pedido 2: nao pago (16.00). Pedido 3: cancelado.
    p1 = client.post(
        '/pedidos/',
        json={
            'tipo': 'balcao',
            'itens': [{'id_menu': loja['x']['id'], 'quantidade': 1}],
        },
        headers=h,
    ).json()
    client.post(
        '/pedidos/',
        json={
            'id_mesa': loja['mesa']['id'],
            'itens': [{'id_menu': loja['suco']['id'], 'quantidade': 2}],
        },
        headers=h,
    )
    p3 = client.post(
        '/pedidos/',
        json={
            'tipo': 'balcao',
            'itens': [{'id_menu': loja['x']['id'], 'quantidade': 4}],
        },
        headers=h,
    ).json()
    client.patch(
        f'/pedidos/{p3["id"]}/status',
        json={'status': 'cancelado', 'motivo': 'teste'},
        headers=h,
    )
    client.post(
        f'/contas/{p1["id_sessao"]}/pagamentos',
        json={
            'valor': '25.50',
            'metodo': 'pix',
            'chave_idempotencia': uuid.uuid4().hex,
        },
        headers=h,
    )
    _entrada(client, h, valor='10.00')
    # Pedido antigo fora do periodo
    antigo = client.post(
        '/pedidos/',
        json={
            'tipo': 'balcao',
            'itens': [{'id_menu': loja['x']['id'], 'quantidade': 10}],
        },
        headers=h,
    ).json()
    with session_factory() as db:
        db.get(Pedido, antigo['id']).created_at = utcnow() - timedelta(days=40)
        db.commit()

    ini = (hoje - timedelta(days=1)).isoformat()
    fim = (hoje + timedelta(days=1)).isoformat()
    r = client.get(
        '/relatorios/resumo', params={'inicio': ini, 'fim': fim}, headers=h
    )
    assert r.status_code == 200, r.text
    res = r.json()
    assert res['total_vendas'] == '41.50'
    assert res['quantidade_pedidos'] == 2
    assert res['ticket_medio'] == '20.75'
    assert res['total_recebido'] == '25.50'
    assert res['outras_entradas'] == '10.00'
    assert res['total_entradas'] == '35.50'
    # mesa (16) + antigo, cuja conta foi aberta hoje (255)
    assert res['pendente_recebimento'] == '271.00'
    assert res['recebido_por_metodo'] == [
        {'rotulo': 'pix', 'valor': '25.50', 'quantidade': 1}
    ]
    assert res['produtos_mais_vendidos'][0]['rotulo'] == 'Suco'
    assert len(res['vendas_por_dia']) == 3
    for campo in ('total_despesas', 'saldo', 'despesas_por_categoria'):
        assert campo not in res
    assert all('despesas' not in d for d in res['vendas_por_dia'])

    vazio = client.get(
        '/relatorios/resumo',
        params={'inicio': '2020-01-01', 'fim': '2020-01-31'},
        headers=h,
    ).json()
    assert vazio['total_vendas'] == '0.00' and vazio['ticket_medio'] == '0.00'

    r = client.get(
        '/relatorios/resumo', params={'inicio': fim, 'fim': ini}, headers=h
    )
    assert r.status_code == 422


def test_exportacoes(client, loja):
    h = loja['h']
    _entrada(client, h, descricao='Repasse de evento', valor='50.10')
    hoje = date.today()
    params = {
        'inicio': (hoje - timedelta(days=1)).isoformat(),
        'fim': (hoje + timedelta(days=1)).isoformat(),
    }
    r = client.get('/relatorios/extrato.csv', params=params, headers=h)
    assert r.status_code == 200
    assert 'text/csv' in r.headers['content-type']
    texto = r.content.decode('utf-8-sig')
    assert 'Repasse de evento' in texto and '50,10' in texto
    assert 'tipo' not in texto.splitlines()[0]

    r = client.get('/relatorios/extrato.pdf', params=params, headers=h)
    assert r.status_code == 200
    assert r.content[:4] == b'%PDF'
