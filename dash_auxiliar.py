import streamlit as st
import pandas as pd

import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import google.auth

import cv2
import requests
import numpy as np

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

def marcar_imagen(url,data,id):
    path = os.path.join('img',f"{id}.jpg")
    if not os.path.isfile(path):
        img_data = requests.get(url).content

        with open(path, 'wb') as handler:
            handler.write(img_data)

    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    colores = [(255,69,0),(127,255,212),(0,128,0),(0,0,255),(223,255,0),(255,249,227),(255,111,97),(247,202,201)]
    objetos = list(set([x['obj_name'] for x in data]))
    colors = {x:colores[i % len(colores)] for i,x in enumerate(objetos)}

    for anotacion in data:
        cuadro = anotacion['bounding_box']
        start_point = (int(cuadro['x_min']), int(cuadro['y_min'])) 
        end_point = (int(cuadro['x_min'] + cuadro['width']) , int(cuadro['y_min'] + cuadro['height'])) 
        # Using cv2.rectangle() method 
        # Draw a rectangle with blue line borders of thickness of 2 px 
        image = cv2.rectangle(image, start_point, end_point, colors[anotacion['obj_name']], 2) 
        #image = cv2.putText(image, anotacion['obj_name'], (int(cuadro['x_min']), int(cuadro['y_min'])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors[anotacion['class_index']], 1)
    
    return image