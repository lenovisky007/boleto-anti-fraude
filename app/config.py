from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-key"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./database.db"

    SCORE_MAX: int = 100
    SCORE_RISCO_BAIXO: int = 30
    SCORE_RISCO_MEDIO: int = 70

    class Config:
        env_file = ".env"


settings = Settings()