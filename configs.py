from pydantic import BaseSettings
from functools import lru_cache
from google.cloud import storage
import google.auth
import os

ERROR_MAQUINA = "No devolvió marcaciones"

class DBSettings(BaseSettings):
    ##### Configuración de la Base de Datos
    BD_SERVER: str
    BD_PORT: int
    BD_NAME: str
    BD_USER: str
    BD_PWD: str
    SSLMODE: str = None
    SSLROOTCERT: str = None
    SSLCERT: str = None
    SSLKEY: str = None

    ##### Configuración de Accesos
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ##### Configuración del correo de alertas
    EMAIL_USERNAME: str
    EMAIL_PWD: str

    ##### Configuración de Máquina
    MC_SERVER: str
    MC_SERVER2: str = None
    MC_PORT: str = None
    MC_PATH: str
    SERVICE: str
    THRESHOLD: float = 0.4
    IMG_FLAG: bool = False

    class Config:
        env_file = ".env"

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