from pydantic import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    DB_NAME: str = "fastdb"
    POOL_MIN_SIZE: int = 2
    POOL_MAX_SIZE: int = 10
    COMMAND_TIMEOUT: int = 5

    class Config:
        env_file = ".env"


settings = Settings()