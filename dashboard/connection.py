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


@st.cache(hash_funcs={Session: id})
def get_all_users(db: Session):
    df = pd.read_sql(db.query(models.User).statement,db.bind)
    return df

@st.cache(hash_funcs={Session: id})
def get_all_challenges(db: Session):
    df = pd.read_sql(db.query(models.Challenge).statement,db.bind)
    return df

@st.cache(hash_funcs={Session: id})
def get_all_respuestas(db: Session):
    df = pd.read_sql(db.query(models.Visit).statement,db.bind)
    return df

@st.cache(hash_funcs={Session: id})
def get_all_images(db: Session):
    df = pd.read_sql(db.query(models.Images).statement,db.bind)
    return df

@st.cache(hash_funcs={Session: id})
def get_all_infaltables(db: Session):
    df = pd.read_sql(db.query(models.Essentials).statement,db.bind)
    return df

@st.cache(hash_funcs={Session: id})
def get_all_faltantes(db: Session):
    df = pd.read_sql(db.query(models.Missings).statement,db.bind)
    return df

@st.cache(hash_funcs={Session: id})
def get_all_tiendas(db: Session):
    df = pd.read_sql(db.query(models.Stores).statement,db.bind)
    return df

@st.cache(hash_funcs={Session: id})
def get_all_grupos(db: Session):
    df = pd.read_sql(db.query(models.Group).statement,db.bind)
    return df

def actualizar(db: Session, counter):
    usuarios = get_all_users(db)
    challenges = get_all_challenges(db)
    respuestas = get_all_respuestas(db)
    imagenes = get_all_images(db)
    infaltables = get_all_infaltables(db)
    faltantes = get_all_faltantes(db)
    faltantes = faltantes.set_index('session_id')
    tiendas = get_all_tiendas(db)
    grupos = get_all_grupos(db)
    fecha = auxiliar.time_now().strftime('%d/%h/%Y %I:%M %p')

    return usuarios, challenges, respuestas, imagenes, infaltables, faltantes, tiendas, grupos, fecha