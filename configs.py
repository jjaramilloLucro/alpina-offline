from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache
from google.cloud import storage
import google.auth
import os

ERROR_MAQUINA = "No devolvió marcaciones"

class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    ##### Configuración de la Base de Datos
    BD_SERVER: str
    BD_PORT: int
    BD_NAME: str
    BD_USER: str
    BD_PWD: str
    SSLMODE: str = Field(default='')
    SSLROOTCERT: str = Field(default='')
    SSLCERT: str = Field(default='')
    SSLKEY: str = Field(default='')

    ##### Configuración de Accesos
    SECRET_KEY: str
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    ##### Configuración del correo de alertas
    EMAIL_USERNAME: str
    EMAIL_PWD: str

    ##### Configuración de Reconocimiento
    MC_CONFIGS: str

@lru_cache()
def get_db_settings():
    return DBSettings()

@lru_cache()
def get_storage():
    credential_path = os.path.join('data','lucro-alpina-20a098d1d018.json')
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path
    credentials_BQ, your_project_id = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    client = storage.Client()
    bucket = client.get_bucket('lucro-alpina-admin_alpina-media')
    return bucket

