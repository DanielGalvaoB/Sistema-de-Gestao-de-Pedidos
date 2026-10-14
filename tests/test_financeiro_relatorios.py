import uuid
from datetime import date, timedelta

from app.core.utils import utcnow
from app.models.models import Pedido


def _cat(client, h, nome, tipo):
    cats = client.get(
        '/financeiro/categorias', params={'tipo': tipo}, headers=h
    ).json()
    return next(c for c in cats if c['nome'] == nome)


def test_categorias_padrao_e_vendas_protegida(client, loja):
    h = loja['h']
    vendas = _cat(client, h, 'Vendas', 'entrada')
    assert vendas['sistema'] is True
    r = client.post(
        '/financeiro/movimentacoes',
        json={
            'tipo': 'entrada',
            'descricao': 'x',
            'id_categoria': vendas['id'],
            'valor': '10',
        },
        headers=h,
    )
    assert r.status_code == 422
    r = client.patch(
        f'/financeiro/categorias/{vendas["id"]}', json={'nome': 'y'}, headers=h
    )
    assert r.status_code == 422


def test_despesa_editar_e_cancelar(client, loja):
    h = loja['h']
    energia = _cat(client, h, 'Energia', 'saida')
    r = client.post(
        '/financeiro/movimentacoes',
        json={
            'tipo': 'saida',
            'descricao': 'Conta de luz',
            'id_categoria': energia['id'],
            'valor': '320.45',
            'metodo_pagamento': 'pix',
        },
        headers=h,
    )
    assert r.status_code == 201
    mid = r.json()['id']
    r = client.patch(
        f'/financeiro/movimentacoes/{mid}', json={'valor': '300.00'}, headers=h
    )
    assert r.json()['valor'] == '300.00'

    entrada = _cat(client, h, 'Outras receitas', 'entrada')
    r = client.patch(
        f'/financeiro/movimentacoes/{mid}',
        json={'id_categoria': entrada['id']},
        headers=h,
    )
    assert r.status_code == 422  # tipo incompativel

    r = client.post(
        f'/financeiro/movimentacoes/{mid}/cancelar',
        json={'motivo': 'lancado errado'},
        headers=h,
    )
    assert r.json()['status'] == 'cancelada'
    assert (
        client.patch(
            f'/financeiro/movimentacoes/{mid}', json={'valor': '1'}, headers=h
        ).status_code
        == 422
    )
    todas = client.get('/financeiro/movimentacoes', headers=h).json()
    assert len(todas) == 1  # nada e apagado


def test_valor_invalido(client, loja):
    h = loja['h']
    energia = _cat(client, h, 'Energia', 'saida')
    for valor in ('0', '-5', '1.234'):
        r = client.post(
            '/financeiro/movimentacoes',
            json={
                'tipo': 'saida',
                'descricao': 'x',
                'id_categoria': energia['id'],
                'valor': valor,
            },
            headers=h,
        )
        assert r.status_code == 422, valor


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
    assert (
        client.patch(
            f'/financeiro/movimentacoes/{mov["id"]}',
            json={'valor': '1'},
            headers=h,
        ).status_code
        == 422
    )
    assert (
        client.post(
            f'/financeiro/movimentacoes/{mov["id"]}/cancelar',
            json={'motivo': 'xxx'},
            headers=h,
        ).status_code
        == 422
    )


def test_relatorio_separa_vendas_recebimentos_e_despesas(
    client, loja, session_factory
):
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
    energia = _cat(client, h, 'Energia', 'saida')
    client.post(
        '/financeiro/movimentacoes',
        json={
            'tipo': 'saida',
            'descricao': 'Luz',
            'id_categoria': energia['id'],
            'valor': '100.00',
        },
        headers=h,
    )
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
    assert res['total_entradas'] == '25.50'
    assert res['total_despesas'] == '100.00'
    assert res['saldo'] == '-74.50'
    assert (
        res['pendente_recebimento'] == '271.00'
    )  # mesa (16) + antigo aberto hoje (255)
    assert res['recebido_por_metodo'] == [
        {'rotulo': 'pix', 'valor': '25.50', 'quantidade': 1}
    ]
    assert res['despesas_por_categoria'][0]['rotulo'] == 'Energia'
    assert res['produtos_mais_vendidos'][0]['rotulo'] == 'Suco'
    assert len(res['vendas_por_dia']) == 3

    # Periodo sem movimento
    vazio = client.get(
        '/relatorios/resumo',
        params={'inicio': '2020-01-01', 'fim': '2020-01-31'},
        headers=h,
    ).json()
    assert vazio['total_vendas'] == '0.00' and vazio['ticket_medio'] == '0.00'

    assert (
        client.get(
            '/relatorios/resumo', params={'inicio': fim, 'fim': ini}, headers=h
        ).status_code
        == 422
    )


def test_exportacoes(client, loja):
    h = loja['h']
    energia = _cat(client, h, 'Energia', 'saida')
    client.post(
        '/financeiro/movimentacoes',
        json={
            'tipo': 'saida',
            'descricao': 'Conta de água',
            'id_categoria': energia['id'],
            'valor': '50.10',
        },
        headers=h,
    )
    hoje = date.today()
    params = {
        'inicio': (hoje - timedelta(days=1)).isoformat(),
        'fim': (hoje + timedelta(days=1)).isoformat(),
    }
    r = client.get('/relatorios/extrato.csv', params=params, headers=h)
    assert r.status_code == 200
    assert 'text/csv' in r.headers['content-type']
    texto = r.content.decode('utf-8-sig')
    assert 'Conta de água' in texto and '50,10' in texto

    r = client.get('/relatorios/extrato.pdf', params=params, headers=h)
    assert r.status_code == 200
    assert r.content[:4] == b'%PDF'
