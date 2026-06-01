from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/url_shortener"
    base_url: str = "http://localhost:8000"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 300

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
