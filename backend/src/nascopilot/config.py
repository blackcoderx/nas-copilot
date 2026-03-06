from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    ollama_base_url: str = "https://ollama.com"
    ollama_model: str = "kimi-k2.5:cloud"
    ollama_api_key: str = ""
    ors_api_key: str = ""
    cors_origins: str = "http://localhost:4321"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_hours: int = 24

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
