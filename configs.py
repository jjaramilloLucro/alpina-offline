from pydantic import BaseSettings
from functools import lru_cache


class DBSettings(BaseSettings):
    ##### Configuración de Accesos
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

@lru_cache()
def get_db_settings():
    return DBSettings()