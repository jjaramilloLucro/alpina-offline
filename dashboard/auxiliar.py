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
    colors = {x:colores[randint(0,len(colores)-1)] for x in objetos}

    for index, cuadro in data.iterrows():
        start_point = (int(cuadro['bounding_box.x_min']), int(cuadro['bounding_box.y_min'])) 
        end_point = (int(cuadro['bounding_box.x_min'] + cuadro['bounding_box.width']) , int(cuadro['bounding_box.y_min'] + cuadro['bounding_box.height'])) 
        end_point = (int(cuadro['bounding_box.x_min'] + cuadro['bounding_box.width']) , int(cuadro['bounding_box.y_min'] + cuadro['bounding_box.height'])) 
        # Using cv2.rectangle() method 
        # Draw a rectangle with blue line borders of thickness of 2 px 
        image = cv2.rectangle(image, start_point, end_point, colors[cuadro['obj_name']], 4) 
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