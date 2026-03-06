from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ors_api_key: str = ""
    cors_origins: str = "http://localhost:4321"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
