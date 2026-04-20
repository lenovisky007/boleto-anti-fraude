from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Boleto Antifraude"
    SECRET_KEY: str = "dev-secret"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./database.db"

    SCORE_MAX: int = 100
    SCORE_ALERTA: int = 60

    class Config:
        env_file = ".env"


settings = Settings()