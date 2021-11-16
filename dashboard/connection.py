import streamlit as st
import models
import pandas as pd
from database import SessionLocal, engine, Base
from sqlalchemy.orm import Session
from dashboard import auxiliar
import time

Base.metadata.create_all(bind=engine)

@st.experimental_singleton(show_spinner= True, suppress_st_warning=True)
def get_session():
    session = SessionLocal()
    return session

def get_all_users(db: Session):
    df = pd.read_sql(db.query(models.User).statement,db.bind)
    return df

def get_all_challenges(db: Session):
    df = pd.read_sql(db.query(models.Challenge).statement,db.bind)
    return df

def get_all_respuestas(db: Session):
    df = pd.read_sql(db.query(models.Visit).statement,db.bind)
    return df

def get_all_images(db: Session):
    df = pd.read_sql(db.query(models.Images).statement,db.bind)
    return df

def get_all_infaltables(db: Session):
    df = pd.read_sql(db.query(models.Essentials).statement,db.bind)
    return df

def get_all_faltantes(db: Session):
    df = pd.read_sql(db.query(models.Missings).statement,db.bind)
    return df

def get_all_tiendas(db: Session):
    df = pd.read_sql(db.query(models.Stores).statement,db.bind)
    return df

def get_all_grupos(db: Session):
    df = pd.read_sql(db.query(models.Group).statement,db.bind)
    return df

@st.cache(hash_funcs={Session: id}, suppress_st_warning=True, allow_output_mutation=True)
def carga_inicial(db: Session):
    print(f'Carga Inicial')
    start_time = time.time()
    usuarios = get_all_users(db)
    challenges = get_all_challenges(db)
    respuestas = get_all_respuestas(db)
    imagenes = get_all_images(db)
    infaltables = get_all_infaltables(db)
    faltantes = get_all_faltantes(db)
    faltantes = faltantes.set_index('session_id')
    tiendas = get_all_tiendas(db)
    grupos = get_all_grupos(db)

    imagenes['created_at'] = pd.to_datetime(imagenes['created_at'],utc=True)
    imagenes['created_at'] = imagenes['created_at'].dt.tz_convert("America/Bogota")
    imagenes['updated_at'] = pd.to_datetime(imagenes['updated_at'],utc=True)
    imagenes['updated_at'] = imagenes['updated_at'].dt.tz_convert("America/Bogota")
    respuestas['created_at'] = pd.to_datetime(respuestas['created_at'],utc=True)
    respuestas['created_at'] = respuestas['created_at'].dt.tz_convert("America/Bogota")
    faltantes['finished_at'] = pd.to_datetime(faltantes['finished_at'],utc=True)
    faltantes['finished_at'] = faltantes['finished_at'].dt.tz_convert("America/Bogota")
    fecha = auxiliar.time_now()
    print("Query time:")
    print("--- %s seconds ---" % (time.time() - start_time))
    return usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos, fecha

def refresh_resp(db:Session, fecha):
    print(fecha)
    df = pd.read_sql(db.query(models.Visit).filter(models.Visit.created_at >= fecha).statement,db.bind)
    return df

def refresh_images(db:Session, fecha):
    print(fecha)
    df = pd.read_sql(db.query(models.Images).filter(models.Visit.created_at >= fecha).statement,db.bind)
    return df

def refresh_faltantes(db:Session, fecha):
    print(fecha)
    df = pd.read_sql(db.query(models.Missings).filter(models.Visit.created_at >= fecha).statement,db.bind)
    return df

def actualizar(db: Session, respuestas, imagenes, faltantes, fecha):
    print(f'Actualizando desde: {fecha}')
    respuestas = pd.concat([refresh_resp(db, fecha),respuestas])
    imagenes = pd.concat([refresh_images(db, fecha),respuestas])
    faltantes = pd.concat([refresh_faltantes(db, fecha),respuestas])
    faltantes = faltantes.set_index('session_id')
    fecha = auxiliar.time_now()

    imagenes['created_at'] = pd.to_datetime(imagenes['created_at'],utc=True)
    imagenes['created_at'] = imagenes['created_at'].dt.tz_convert("America/Bogota")
    imagenes['updated_at'] = pd.to_datetime(imagenes['updated_at'],utc=True)
    imagenes['updated_at'] = imagenes['updated_at'].dt.tz_convert("America/Bogota")
    respuestas['created_at'] = pd.to_datetime(respuestas['created_at'],utc=True)
    respuestas['created_at'] = respuestas['created_at'].dt.tz_convert("America/Bogota")
    faltantes['finished_at'] = pd.to_datetime(faltantes['finished_at'],utc=True)
    faltantes['finished_at'] = faltantes['finished_at'].dt.tz_convert("America/Bogota")

   
    return respuestas, imagenes, faltantes, fecha