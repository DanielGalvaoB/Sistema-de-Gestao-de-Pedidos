from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def _connect_args(url: str) -> dict:
    if url.startswith('sqlite'):
        return {'check_same_thread': False}
    return {}


engine = create_engine(
    settings.DATABASE_URL, connect_args=_connect_args(settings.DATABASE_URL)
)


@event.listens_for(Engine, 'connect')
def _sqlite_pragmas(dbapi_connection, connection_record):
    # O SQLite so aplica foreign keys quando esta pragma esta ligada
    module = type(dbapi_connection).__module__
    if 'sqlite' in module:
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
