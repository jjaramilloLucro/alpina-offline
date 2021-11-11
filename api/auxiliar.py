import os, json, requests, base64, math, random
import configs
from api import connection
from threading import Thread
import cv2
import numpy as np
import pytz, datetime
import urllib.request

settings = configs.get_db_settings()
bucket = configs.get_storage()

def decode(url):
    img = base64.b64encode(requests.get(url).content)
    return img.decode('utf-8')

def actualizar_imagenes(db, imagenes, session_id):
    threads = list()
    for foto in imagenes:
        t = Thread(target=identificar_producto, args=(db, foto['img'],foto['id'],session_id))
        threads.append(t)

    [threads[i].start() for i in range(len(threads))]
    [threads[i].join() for i in range(len(threads))]

    db.commit()

def identificar_producto(db, imagen, id, session_id):
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
        connection.actualizar_imagen(db, id, data, marcada, error)

    except Exception as e:
        try:
            res1 = requests.post("http://retailappml.eastus.cloudapp.azure.com:8081/detect", json=post_data)
            prod = json.loads(res1.text)
            if 'resultlist' in prod:
                data = prod['resultlist']
                marcada = None
                if data:
                    marcada = marcar_imagen(id, imagen, data, session_id)
                error = None
            else:
                data = list()
                error = "No hubo reconocimiento"
                marcada = None

            connection.actualizar_imagen(db, id, data, marcada, error)
                
        except Exception as e:
            connection.actualizar_imagen(db, id, list(), None, str(e))
            print(f"Error en imagen {id}: " + str(e))
            return str(e)
    

    return prod

def marcar_imagen(id, original, data, session_id):
    path = os.path.join('img',f"{id}.jpg")

    url_response = urllib.request.urlopen(original)
    image = cv2.imdecode(np.array(bytearray(url_response.read()), dtype=np.uint8), -1)

    colores = [(255,69,0),(127,255,212),(0,128,0),(0,0,255),(223,255,0),(255,249,227),(255,111,97),(247,202,201)]
    objetos = list(set([x['obj_name'] for x in data]))
    colors = {x:colores[i % len(colores)] for i,x in enumerate(objetos)}

    
    for anotacion in data:
        cuadro = anotacion['bounding_box']
        start_point = (int(cuadro['x_min']), int(cuadro['y_min'])) 
        end_point = (int(cuadro['x_min'] + cuadro['width']) , int(cuadro['y_min'] + cuadro['height'])) 
        # Using cv2.rectangle() method 
        # Draw a rectangle with blue line borders of thickness of 2 px 
        image = cv2.rectangle(image, start_point, end_point, colors[anotacion['obj_name']], 3) 
        #image = cv2.putText(image, anotacion['obj_name'], (int(cuadro['x_min']), int(cuadro['y_min'])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors[anotacion['class_index']], 1)
    
    #Create the legend
    x, y, z = image.shape
    h = 20* len(objetos) + 3
    # First we crop the sub-rect from the image
    
    white_rect = np.full((h,y, 3), 255, np.uint8)
    result = np.concatenate([image,white_rect])

    # Putting the image back to its position
    
    h=3
    for objeto in objetos:
        result = cv2.rectangle(result, (11,h+x), (16,h+x+10), colors[objeto], -1)
        result = cv2.putText(result, objeto, (20,h+x+8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1)
        h += 20
    
    # convert to jpeg and save in variable
    cv2.imwrite(path,result)

    save = f"mark_images/{session_id}/{id}.jpg"
    object_name_in_gcs_bucket = bucket.blob(save)
    object_name_in_gcs_bucket.upload_from_filename(path)
    
    return 'https://storage.googleapis.com/lucro-alpina-admin_alpina-media/'+save

def guardar_imagenes(db, respuesta):
    threads = list()
    for foto in respuesta['imagenes']:
        t = Thread(target=upload_image, args=(foto, respuesta, db))
        threads.append(t)

    [threads[i].start() for i in range(len(threads))]
    [threads[i].join() for i in range(len(threads))]
    db.commit()


def upload_image(foto, respuesta, db):
    img_data = foto['img']
    path = os.path.join('img',f"{foto['id']}.jpg")

    with open(path, 'wb') as handler:
        handler.write(img_data)

    save = f"original_images/{respuesta['uid']}/{respuesta['document_id']}/{respuesta['session_id']}/{foto['id']}.jpg"
    object_name_in_gcs_bucket = bucket.blob(save)

    object_name_in_gcs_bucket.upload_from_filename(path)

    ruta = 'https://storage.googleapis.com/lucro-alpina-admin_alpina-media/'+save
    foto['img'] = ruta
    connection.guardar_url_original(db, foto['id'],ruta)

def save_answer(db, respuesta):
    connection.guardar_resultados_imagen(db, respuesta)
    guardar_imagenes(db, respuesta)
    imagenes = respuesta['imagenes']
    del respuesta['imagenes']
    connection.guardar_resultados(db, respuesta)
    return imagenes

def session_id(db):
    id = create_session()
    while not connection.existe_session(db, id):
        id = create_session()

    return id


def create_session():
    cod = []
    d = int(datetime.datetime.now().timestamp())
    m = (math.floor(random.random() * d + d ** (2)))
    for i in range(6):
        d = int(datetime.datetime.now().timestamp())
        r = (d + m*i) % (16**4)
        m = r
        a = str(hex(r))
        cod.append(a[2:])

    return ''.join(cod)

def time_now():
    dateti = datetime.datetime.now()
    bogota = pytz.timezone('America/Bogota')

    with_timezone = bogota.localize(dateti)
    
    return with_timezone