from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASS: str = "change-me"
    DB_NAME: str = "fastdb"
    POOL_MIN_SIZE: int = 2
    POOL_MAX_SIZE: int = 10
    COMMAND_TIMEOUT: int = 5
    FAILURE_RATE: float = 0.0

    @validator("FAILURE_RATE", pre=True)
    def normalize_failure_rate(cls, value):
        try:
            return min(1.0, max(0.0, float(value or 0)))
        except (TypeError, ValueError):
            return 0.0

    class Config:
        env_file = ".env"


settings = Settings()