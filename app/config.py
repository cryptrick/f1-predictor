from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://links:changeme@db:5432/links"
    redis_url: str = "redis://redis:6379/0"

    telegram_bot_token: str = ""
    telegram_allowed_user_ids: str = ""

    ingest_tokens: str = ""

    @property
    def allowed_user_id_set(self) -> set[int]:
        return {int(x) for x in self.telegram_allowed_user_ids.split(",") if x.strip()}

    @property
    def ingest_token_set(self) -> set[str]:
        return {x.strip() for x in self.ingest_tokens.split(",") if x.strip()}


settings = Settings()
