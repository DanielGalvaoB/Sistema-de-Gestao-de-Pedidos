import secrets
import unicodedata
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

from app.config import settings

CENTAVO = Decimal('0.01')


def q2(valor) -> Decimal:
    """Normaliza um valor monetario para 2 casas decimais."""
    if valor is None:
        return Decimal('0.00')
    if not isinstance(valor, Decimal):
        valor = Decimal(str(valor))
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def utcnow() -> datetime:
    """Datahora UTC sem tzinfo (padrao de armazenamento do banco)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def local_tz() -> ZoneInfo:
    return ZoneInfo(settings.APP_TIMEZONE)


def to_local(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc).astimezone(local_tz())


def periodo_utc(inicio: date, fim: date) -> tuple[datetime, datetime]:
    """Converte [inicio, fim] (datas locais, inclusivas) para UTC naive."""
    tz = local_tz()
    ini = datetime.combine(inicio, time.min, tz)
    end = datetime.combine(fim + timedelta(days=1), time.min, tz)
    return (
        ini.astimezone(timezone.utc).replace(tzinfo=None),
        end.astimezone(timezone.utc).replace(tzinfo=None),
    )


def novo_token(nbytes: int = 12) -> str:
    return secrets.token_urlsafe(nbytes)


def slugify(texto: str) -> str:
    norm = unicodedata.normalize('NFKD', texto)
    ascii_txt = norm.encode('ascii', 'ignore').decode().lower()
    partes = ''.join(c if c.isalnum() else '-' for c in ascii_txt).split('-')
    return '-'.join(p for p in partes if p) or 'loja'
