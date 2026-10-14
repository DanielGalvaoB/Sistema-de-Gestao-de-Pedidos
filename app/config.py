from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8', extra='ignore'
    )

    DATABASE_URL: str = 'sqlite:///./peccai.db'
    SECRET_KEY: str = 'troque-esta-chave-em-producao'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12
    JWT_ALGORITHM: str = 'HS256'
    BCRYPT_ROUNDS: int = 12
    # Lista separada por virgula
    CORS_ORIGINS: str = 'http://localhost:5173,http://127.0.0.1:5173'
    # URL publica do frontend, usada nos links dos QR Codes
    FRONTEND_URL: str = 'http://localhost:5173'
    APP_TIMEZONE: str = 'America/Sao_Paulo'

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(',') if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
