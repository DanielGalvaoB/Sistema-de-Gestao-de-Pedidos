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
