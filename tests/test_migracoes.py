from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command

RAIZ = Path(__file__).resolve().parents[1]


def _config(url: str) -> Config:
    cfg = Config(str(RAIZ / 'alembic.ini'))
    cfg.set_main_option('script_location', str(RAIZ / 'alembic'))
    cfg.set_main_option('sqlalchemy.url', url)
    cfg.attributes['url_definida'] = True
    return cfg


def test_banco_novo_criado_somente_por_migracoes(tmp_path):
    url = f'sqlite:///{(tmp_path / "novo.db").as_posix()}'
    cfg = _config(url)
    command.upgrade(cfg, 'head')

    eng = create_engine(url)
    tabelas = set(inspect(eng).get_table_names())
    esperado = {
        'estabelecimento',
        'usuario',
        'categoria',
        'menu',
        'historico_preco',
        'mesa',
        'sessao_atendimento',
        'pedido',
        'item_pedido',
        'historico_status_pedido',
        'pagamento',
        'cobranca_pix',
        'categoria_financeira',
        'movimentacao_financeira',
    }
    assert esperado <= tabelas
    # Modelos e migracoes sincronizados (falha se faltar migracao)
    command.check(cfg)

    command.downgrade(cfg, 'base')
    with eng.connect() as conn:
        restantes = (
            conn
            .execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            .scalars()
            .all()
        )
    assert set(restantes) <= {'alembic_version'}
    eng.dispose()


def test_foreign_keys_ativas_no_sqlite():
    from app.database import engine

    with engine.connect() as conn:
        assert conn.execute(text('PRAGMA foreign_keys')).scalar() == 1


def test_migracao_preserva_pagamentos_existentes(tmp_path):
    """Atualiza um banco com pagamentos ja referenciados pelo financeiro."""
    url = f'sqlite:///{(tmp_path / "antigo.db").as_posix()}'
    cfg = _config(url)
    command.upgrade(cfg, '78a468eea797')
    eng = create_engine(url)
    with eng.begin() as conn:
        conn.exec_driver_sql(
            'INSERT INTO estabelecimento (id, nome_loja, slug, chave_pix, '
            'nome_titular, cidade, email, ativo, tempo_preparo_padrao_min, '
            'alerta_atraso_percentual, taxa_servico_percentual, created_at) '
            "VALUES (1,'L','l','k','T','SP','a@a.com',1,20,80,0,'2026-01-01')"
        )
        conn.exec_driver_sql(
            'INSERT INTO sessao_atendimento (id, id_estabelecimento, tipo, '
            'status, desconto, acrescimo, aberta_em) '
            "VALUES (1,1,'balcao','aberta',0,0,'2026-01-01')"
        )
        conn.exec_driver_sql(
            'INSERT INTO categoria_financeira (id, id_estabelecimento, nome, '
            "tipo, ativo, sistema) VALUES (1,1,'Vendas','entrada',1,1)"
        )
        conn.exec_driver_sql(
            'INSERT INTO pagamento (id, id_estabelecimento, id_sessao, valor, '
            'metodo, status, origem, chave_idempotencia, data_hora) '
            "VALUES (1,1,1,10,'pix','confirmado','manual','chave-1',"
            "'2026-01-01')"
        )
        conn.exec_driver_sql(
            'INSERT INTO movimentacao_financeira (id, id_estabelecimento, '
            'tipo, descricao, id_categoria, valor, data_hora, id_pagamento, '
            "status, created_at) VALUES (1,1,'entrada','x',1,10,"
            "'2026-01-01',1,'ativa','2026-01-01')"
        )
    eng.dispose()

    command.upgrade(cfg, 'head')
    command.check(cfg)
    eng = create_engine(url)
    with eng.connect() as conn:
        assert (
            conn.execute(text('SELECT count(*) FROM pagamento')).scalar() == 1
        )
        assert conn.execute(text('PRAGMA foreign_key_check')).all() == []
    eng.dispose()
