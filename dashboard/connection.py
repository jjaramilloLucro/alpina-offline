import streamlit as st
import models
import pandas as pd
from database import SessionLocal, engine, Base
from sqlalchemy.orm import Session
from dashboard import auxiliar

Base.metadata.create_all(bind=engine)

@st.experimental_singleton(show_spinner= True, suppress_st_warning=True)
def get_session():
    session = SessionLocal()
    return session


@st.cache(hash_funcs={Session: id}, suppress_st_warning=False)
def get_all_users(db: Session, counter):
    df = pd.read_sql(db.query(models.User).statement,db.bind)
    return df

@st.cache(hash_funcs={Session: id}, suppress_st_warning=False)
def get_all_challenges(db: Session, counter):
    df = pd.read_sql(db.query(models.Challenge).statement,db.bind)
    return df

@st.cache(hash_funcs={Session: id}, suppress_st_warning=False)
def get_all_respuestas(db: Session, counter):
    df = pd.read_sql(db.query(models.Visit).statement,db.bind)
    return df

@st.cache(hash_funcs={Session: id}, suppress_st_warning=False)
def get_all_images(db: Session, counter):
    df = pd.read_sql(db.query(models.Images).statement,db.bind)
    return df

@st.cache(hash_funcs={Session: id}, suppress_st_warning=False)
def get_all_infaltables(db: Session, counter):
    df = pd.read_sql(db.query(models.Essentials).statement,db.bind)
    return df

@st.cache(hash_funcs={Session: id}, suppress_st_warning=False)
def get_all_faltantes(db: Session, counter):
    df = pd.read_sql(db.query(models.Missings).statement,db.bind)
    return df

@st.cache(hash_funcs={Session: id}, suppress_st_warning=False)
def get_all_tiendas(db: Session, counter):
    df = pd.read_sql(db.query(models.Stores).statement,db.bind)
    return df

@st.cache(hash_funcs={Session: id}, suppress_st_warning=False)
def get_all_grupos(db: Session, counter):
    df = pd.read_sql(db.query(models.Group).statement,db.bind)
    return df

def actualizar(db: Session, counter):
    usuarios = get_all_users(db, counter)
    challenges = get_all_challenges(db, counter)
    respuestas = get_all_respuestas(db, counter)
    imagenes = get_all_images(db, counter)
    infaltables = get_all_infaltables(db, counter)
    faltantes = get_all_faltantes(db, counter)
    faltantes = faltantes.set_index('session_id')
    tiendas = get_all_tiendas(db, counter)
    grupos = get_all_grupos(db, counter)
    fecha = auxiliar.time_now().strftime('%d/%h/%Y %I:%M %p')

    imagenes['created_at'] = pd.to_datetime(imagenes['created_at'],utc=True)
    imagenes['created_at'] = imagenes['created_at'].dt.tz_convert("America/Bogota")
    imagenes['updated_at'] = pd.to_datetime(imagenes['updated_at'],utc=True)
    imagenes['updated_at'] = imagenes['updated_at'].dt.tz_convert("America/Bogota")
    respuestas['created_at'] = pd.to_datetime(respuestas['created_at'],utc=True)
    respuestas['created_at'] = respuestas['created_at'].dt.tz_convert("America/Bogota")
    faltantes['finished_at'] = pd.to_datetime(faltantes['created_at'],utc=True)
    faltantes['finished_at'] = faltantes['created_at'].dt.tz_convert("America/Bogota")

    return usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos, fecha