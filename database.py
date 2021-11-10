from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from configs import get_db_settings

settings = get_db_settings()

SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.BD_USER}:{settings.BD_PWD}@{settings.BD_SERVER}:{settings.BD_PORT}/{settings.BD_NAME}"

if settings.SSLMODE:
    SQLALCHEMY_DATABASE_URL += f"?sslmode={settings.SSLMODE}&sslrootcert={settings.SSLROOTCERT}&sslcert={settings.SSLCERT}&sslkey={settings.SSLKEY}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
