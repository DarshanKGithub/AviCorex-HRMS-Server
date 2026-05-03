from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'HRMS API'
    secret_key: str = 'change-this-secret'
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 480
    database_url: str = 'sqlite:///./hrms.db'
    frontend_origins: str = 'http://localhost:3000,http://127.0.0.1:3000'

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(',') if origin.strip()]


@lru_cache

def get_settings() -> Settings:
    return Settings()


settings = get_settings()
