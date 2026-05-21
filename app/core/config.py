from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'HRMS API'
    secret_key: str = '00ee418573243bd9d17d1af8f264fa85df3f8039d281b229031fdaeb99f97bd4'
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 480
    database_url: str = 'sqlite:///./hrms.db'
    frontend_origins: str = 'http://localhost:3000,http://127.0.0.1:3000,https://avi-corex-hrms-ui.vercel.app/,https://hrms.greatertechhub.com'
    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None
    razorpay_webhook_secret: str | None = None

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    @property
    def sqlalchemy_database_url(self) -> str:
        """Return a SQLAlchemy URL compatible with installed Postgres driver."""
        raw = self.database_url.strip()
        if raw.startswith('postgresql+'):  # driver already specified
            return raw
        if raw.startswith('postgres://'):
            return raw.replace('postgres://', 'postgresql+psycopg://', 1)
        if raw.startswith('postgresql://'):
            return raw.replace('postgresql://', 'postgresql+psycopg://', 1)
        return raw

    @property
    def cors_origins(self) -> list[str]:
        return [origin.rstrip('/').strip() for origin in self.frontend_origins.split(',') if origin.strip()]


@lru_cache

def get_settings() -> Settings:
    return Settings()


settings = get_settings()
