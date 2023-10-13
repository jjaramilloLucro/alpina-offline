from random import randint
import streamlit as st
import cv2
import urllib.request
import numpy as np
import pytz, datetime

def marcar_imagen(url,data,id):
    image = download_image(url)
    print('Procesando...')
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    colores = [(255,69,0),(127,255,212),(0,128,0),(6, 214, 160  ),(223,255,0),(148, 10, 24),(233, 180, 76),(209, 219, 66),(112, 48, 48), (47, 52, 59), 
                (126, 130, 122), (227, 205, 164), (199, 121, 102), (150, 202, 45)]
    objetos = list(data['obj_name'].unique())
    colores = [(255,69,0),(127,255,212),(0,128,0),(0,0,255),(223,255,0),(255,249,227),(255,111,97),(247,202,201)]
    objetos = list(set([x['obj_name']['Nombre'] if isinstance(x['obj_name'], dict) else x['obj_name'] for x in data]))
    colors = {x:colores[i % len(colores)] for i,x in enumerate(objetos)}

    
    for anotacion in data:
        cuadro = anotacion['bounding_box']
        nombre = anotacion['obj_name']['Nombre'] if isinstance(anotacion['obj_name'], dict) else anotacion['obj_name']
        start_point = (int(cuadro['x_min']), int(cuadro['y_min']))
        #end_point = (int(cuadro['x_min'] + cuadro['width']) , int(cuadro['y_min'] + cuadro['height']))
        end_point = (int(cuadro['x_max']) , int(cuadro['y_max']))
        # Using cv2.rectangle() method
        # Draw a rectangle with blue line borders of thickness of 2 px
        image = cv2.rectangle(image, start_point, end_point, colors[nombre], 3)
        #image = cv2.putText(image, anotacion['obj_name'], (int(cuadro['x_min']), int(cuadro['y_min'])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors[anotacion['class_index']], 1)

    return image, colors

@st.cache(suppress_st_warning=True, allow_output_mutation=True)
def download_image(url):
    print("Descargando...")
    url_response = urllib.request.urlopen(url)
    img = cv2.imdecode(np.array(bytearray(url_response.read()), dtype=np.uint8), -1)
    return img

def time_now():
    dateti = datetime.datetime.now()
    bogota = pytz.timezone('America/Bogota')

    with_timezone = bogota.localize(dateti)
    
    return with_timezone