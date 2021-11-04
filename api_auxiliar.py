import streamlit as st
import pandas as pd

import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import google.auth


@st.experimental_singleton(show_spinner= True, suppress_st_warning=True)
def inicializacion():
    print('empezando')
    credential_path = os.path.join('data','lucro-alpina-20a098d1d018.json')
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path
    credentials_BQ, your_project_id = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    #Conexion a Firebase Cloud Firestore
    url = os.path.join('data','lucro-alpina-firebase-adminsdk-yeun4-0e168872c1.json')
    cred = credentials.Certificate(url)
    firebase_admin.initialize_app(cred, {
        'projectId': 'lucro-alpina',
    })


def get_all_users():
    db = firestore.client()
    doc_ref = db.collection(u'users')
    query = doc_ref.stream()

    users = [doc.to_dict() for doc in query]
	
    return users

def get_all_challenges():
    db = firestore.client()
    doc_ref = db.collection(u'challenges')
    query = doc_ref.stream()

    users = [doc.to_dict() for doc in query]
	
    return users

def get_all_respuestas():
    db = firestore.client()
    doc_ref = db.collection(u'respuestas')
    query = doc_ref.stream()

    users = [doc.to_dict() for doc in query]
	
    return users

def get_all_images():
    db = firestore.client()
    doc_ref = db.collection(u'images')
    query = doc_ref.stream()
    users = list()
    for doc in query:
        user = doc.to_dict()
        user['document_id'] = doc.id
        users.append(user)
	
    return users

def get_all_inflatables():
    db = firestore.client()
    doc_ref = db.collection(u'infaltables')
    query = doc_ref.stream()

    users = [doc.to_dict() for doc in query]

    return users

def get_all_faltantes():
    db = firestore.client()
    doc_ref = db.collection(u'faltantes')
    query = doc_ref.stream()

    users = [doc.to_dict() for doc in query]
	
    return users

@st.cache(suppress_st_warning=True, allow_output_mutation=True, ttl=900)
def carga_inicial():
    print('inicializando')
    inicializacion()
    return actualizar_tablas()

def actualizar_tablas():
    usuarios = pd.DataFrame(get_all_users())
    challenges = pd.DataFrame(get_all_challenges())
    respuestas = pd.DataFrame(get_all_respuestas())
    respuestas['created_at'] = pd.to_datetime(respuestas['created_at'],utc=True)
    respuestas['created_at'] = respuestas['created_at'].dt.tz_convert("America/Bogota")
    respuestas.rename(columns={"document_id": "challenge_id"})
    imagenes = pd.DataFrame(get_all_images())
    imagenes['created_at'] = pd.to_datetime(imagenes['created_at'],utc=True)
    imagenes['updated_at'] = pd.to_datetime(imagenes['updated_at'],utc=True)
    imagenes['updated_at'] = imagenes['updated_at'].dt.tz_convert("America/Bogota")
    infaltables = pd.DataFrame(get_all_inflatables())
    faltantes = pd.DataFrame(get_all_faltantes())

    return usuarios, challenges, respuestas, imagenes, infaltables, faltantes
