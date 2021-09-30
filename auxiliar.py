import os, json, requests, base64
import configs, connection
from threading import Thread
from google.cloud import storage
import cv2, time
import numpy as np
import pytz, datetime

settings = configs.get_db_settings()

def decode(url):
    img = base64.b64encode(requests.get(url).content)
    return img.decode('utf-8')

def identificar_producto(imagen, id, session_id):

    img = base64.b64encode(requests.get(imagen, verify=False).content)
    post_data = {
            "image": img.decode('utf-8'),
            "service": settings.SERVICE,        
            "thresh": settings.THRESHOLD,
            "get_img_flg": settings.IMG_FLAG}
    
    try:
        
        res1 = requests.post("http://retailappml.eastus.cloudapp.azure.com:8081/detect", json=post_data)
        prod = json.loads(res1.text)
        if 'resultlist' in prod:
            data = prod['resultlist']
            marcada = marcar_imagen(id, imagen, data, session_id)
            error = None
        else:
            data = list()
            error = "No hubo reconocimiento"
            marcada = None

        connection.actualizar_imagen(id, data, imagen, marcada, error)
            
    except Exception as e:
        try:
            res1 = requests.post("http://retailappml.eastus.cloudapp.azure.com:8081/detect", json=post_data)
            prod = json.loads(res1.text)
            if 'resultlist' in prod:
                data = prod['resultlist']
                marcada = marcar_imagen(id, imagen, data, session_id)
                error = None
            else:
                data = list()
                error = "No hubo reconocimiento"
                marcada = None

            connection.actualizar_imagen(id, data, imagen, marcada, error)
                
        except Exception as e:
            connection.actualizar_imagen(id, list(), imagen, None, str(e))
            print(f"Error en imagen {id}: " + str(e))
            return str(e)
    
    return prod

def actualizar_imagenes(imagenes, session_id):
    threads = list()
    for foto in imagenes:
        t = Thread(target=identificar_producto, args=(foto['img'],foto['id'],session_id))
        threads.append(t)

    [threads[i].start() for i in range(len(threads))]
    [threads[i].join() for i in range(len(threads))]

def guardar_imagenes(respuesta):
    threads = list()
    for foto in respuesta['imagenes']:
        t = Thread(target=upload_image, args=(foto, respuesta))
        threads.append(t)

    [threads[i].start() for i in range(len(threads))]
    [threads[i].join() for i in range(len(threads))]

def marcar_imagen(id, original, data, session_id):
    img_data = requests.get(original).content
    path = os.path.join('img',f"{id}.jpg")

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
    
    #Create the legend
    w = len(max(objetos, key=len))*9 + 20
    x, y = 10, 10
    h = 20* len(objetos) + 3
    # First we crop the sub-rect from the image
    sub_img = image[y:y+h, x:x+w]
    white_rect = np.full(sub_img.shape, 255, np.uint8)
    res = cv2.addWeighted(sub_img, 0.5, white_rect, 0.5, 1.0)

    # Putting the image back to its position
    image[y:y+h, x:x+w] = res
    h=3
    for objeto in objetos:
        image = cv2.rectangle(image, (11,h+x), (16,h+x+10), colors[objeto], -1)
        image = cv2.putText(image, objeto, (20,h+x+8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1)
        h += 20
    
    # convert to jpeg and save in variable
    image_bytes = cv2.imencode('.jpg', image)[1].tobytes()
    with open(path, 'wb') as handler:
        handler.write(image_bytes)

    save = f"mark_images/{session_id}/{id}.jpg"
    
    client = storage.Client()
    bucket = client.get_bucket('lucro-alpina-admin_alpina-media')
    
    object_name_in_gcs_bucket = bucket.blob(save)

    object_name_in_gcs_bucket.upload_from_filename(path)
    os.remove(path)
    
    return 'https://storage.googleapis.com/lucro-alpina-admin_alpina-media/'+save

def upload_image(foto, respuesta):
    img_data = foto['img']
    path = os.path.join('img',f"{foto['id']}.jpg")

    with open(path, 'wb') as handler:
        handler.write(img_data)

    client = storage.Client()
    bucket = client.get_bucket('lucro-alpina-admin_alpina-media')
    save = f"original_images/{respuesta['uid']}/{respuesta['document_id']}/{respuesta['session_id']}/{foto['id']}.jpg"
    object_name_in_gcs_bucket = bucket.blob(save)

    object_name_in_gcs_bucket.upload_from_filename(path)
    os.remove(path)

    foto['img'] = 'https://storage.googleapis.com/lucro-alpina-admin_alpina-media/'+save


def save_answer(respuesta):
    connection.guardarResultadosImagen(respuesta)
    guardar_imagenes(respuesta)
    imagenes = respuesta['imagenes']
    del respuesta['imagenes']
    connection.guardarResultados(respuesta)
    return imagenes

def session_id():
    return connection.documento_temporal()

def time_now():
    dateti = datetime.datetime.now()
    bogota = pytz.timezone('America/Bogota')

    with_timezone = bogota.localize(dateti)
    
    return with_timezone