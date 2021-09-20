import os, json, requests, base64
import configs, connection
from threading import Thread
from google.cloud import storage
import cv2
from random import randint

settings = configs.get_db_settings()

def decode(url):
    img = base64.b64encode(requests.get(url).content)
    return img.decode('utf-8')

def identificar_producto(imagen, id):
    img = base64.b64encode(requests.get(imagen).content)
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
            marcada = marcar_imagen(id, imagen, data)
        else:
             data = "No hubo reconocimiento"
             marcada = None

        connection.actualizar_imagen(id, data, imagen, marcada)
            
    except Exception as e:
        connection.actualizar_imagen(id, str(e), imagen, None)
    
    return prod

def actualizar_imagenes(imagenes):
    threads = list()
    for foto in imagenes:
        t = Thread(target=identificar_producto, args=(foto['img'],foto['id']))
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

def marcar_imagen(id, original, data):
    img_data = requests.get(original).content
    path = os.path.join('img',f"{id}.png")

    with open(path, 'wb') as handler:
        handler.write(img_data)

    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
   
    colors = {x['class_index']:(randint(0, 255), randint(0, 255), randint(0, 255)) for x in data}
    
    for anotacion in data:
        cuadro = anotacion['bounding_box']
        start_point = (int(cuadro['x_min']), int(cuadro['y_min'])) 
        end_point = (int(cuadro['x_min'] + cuadro['width']) , int(cuadro['y_min'] + cuadro['height'])) 
        # Using cv2.rectangle() method 
        # Draw a rectangle with blue line borders of thickness of 2 px 
        image = cv2.rectangle(image, start_point, end_point, colors[anotacion['class_index']], 2) 
    
     # convert to jpeg and save in variable
    image_bytes = cv2.imencode('.jpg', image)[1].tobytes()
    with open(path, 'wb') as handler:
        handler.write(image_bytes)

    client = storage.Client()
    bucket = client.get_bucket('lucro-alpina-admin_alpina-media')
    save = f"mark_images/{id}.png"
    object_name_in_gcs_bucket = bucket.blob(save)

    object_name_in_gcs_bucket.upload_from_filename(path)
    os.remove(path)

    return 'https://storage.googleapis.com/lucro-alpina-admin_alpina-media/'+save

def upload_image(foto, respuesta):
    img_data = foto['img']
    path = os.path.join('img',f"{foto['id']}.png")

    with open(path, 'wb') as handler:
        handler.write(img_data)

    client = storage.Client()
    bucket = client.get_bucket('lucro-alpina-admin_alpina-media')
    save = f"original_images/{respuesta['uid']}/{respuesta['document_id']}/{foto['id']}.png"
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