import os, json, requests, base64
import configs
from api import connection
from threading import Thread
import cv2
import numpy as np
import pytz, datetime
import urllib.request
from api.correo import Mail
import uuid

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

    try:
        db.commit()
    except:
        db.revert()
        db.commit()

def identificar_producto(db, imagen, id, session_id):
    try:
        image = [('image', (requests.get(imagen).content))]
    except:
        image = [('image', (requests.get(imagen).content))]
    try:
        print("Primer Intento")
        path = f"http://{settings.MC_SERVER}"
        if settings.MC_PORT:
            path += f":{settings.MC_PORT}"
        
        path += f"/{settings.MC_PATH}"
        res1 = requests.post(path, files=image, verify=False)
        prod = res1.json()["results"]
        if prod:
            data = prod[0]
            data = change_variables(data)
            marcada = marcar_imagen(id, imagen, data, session_id)
            error = None
        else:
            data = list()
            error = configs.ERROR_MAQUINA
            marcada = None
        connection.actualizar_imagen(db, id, data, marcada, error, "AZURE")
        return prod
    except Exception as e:
        print(f"Primer error: " + str(e))
        connection.actualizar_imagen(db, id, list(), None, str(e), None)
        correo_falla_servidor(str(e),id,"AWS-1",path)


    
    try:
        print("Segundo intento AWS")
        if settings.MC_SERVER2:
            path = f"http://{settings.MC_SERVER2}"
        else:
            path = f"http://{settings.MC_SERVER}"

        if settings.MC_PORT:
            path += f":{settings.MC_PORT}"
        
        path += f"/{settings.MC_PATH}"
        res1 = requests.post(path, files=image, verify=False)
        prod = res1.json()["results"]
        if prod:
            data = prod[0]
            data = change_variables(data)
            marcada = marcar_imagen(id, imagen, data, session_id)
            error = None
        else:
            data = list()
            error = configs.ERROR_MAQUINA
            marcada = None
        connection.actualizar_imagen(db, id, data, marcada, error, "AWS-2")
        return prod

    except Exception as e:
        connection.actualizar_imagen(db, id, list(), None, str(e), None)
        #print(f"Error en imagen {id}: " + str(e))
        #correo_falla_servidor(str(e),id,"AWS-2",path)
        return str(e)
    

def marcar_imagen(id, original, data, session_id):
    """
    Marca una Imagen según sus anotaciones
    Params.
        - id. ID de la imagen.
        - original. URL de la imagen original a marcar.
        - data. Anotaciones para marcar.
        - session_id. Id de la sesión para guardarlo en la ruta del storage
    Returns.
        - URL de la ubicación con la imagen marcada
    """
    path = os.path.join('img',f"{id}.jpg") #Lee la ruta local donde se guardará

    url_response = urllib.request.urlopen(original) #Descarga la imagen del link
    image = cv2.imdecode(np.array(bytearray(url_response.read()), dtype=np.uint8), -1) #Lee la imagen

    colores = [(255,69,0),(127,255,212),(0,128,0),(0,0,255),(223,255,0),(255,249,227),(255,111,97),(247,202,201)]
    objetos = list(set([x['obj_name'] for x in data]))
    colors = {x:colores[i % len(colores)] for i,x in enumerate(objetos)}

    
    for anotacion in data:
        cuadro = anotacion['bounding_box']
        start_point = (int(cuadro['x_min']), int(cuadro['y_min'])) 
        end_point = (int(cuadro['x_min'] + cuadro['width']) , int(cuadro['y_min'] + cuadro['height']))
        #end_point = (int(cuadro['x_max']) , int(cuadro['y_max'])) 
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

    #Salva en el storage de Google
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
    try:
        db.commit()
    except:
        db.revert()
        db.commit()


def upload_image(foto, respuesta, db):
    img_data = foto['img']
    path = os.path.join('img',f"{foto['id']}.jpg")

    with open(path, 'wb') as handler:
        handler.write(img_data)

    save = f"original_images/{respuesta['session_id']}/{foto['id']}.jpg"
    object_name_in_gcs_bucket = bucket.blob(save)

    object_name_in_gcs_bucket.upload_from_filename(path)

    ruta = 'https://storage.googleapis.com/lucro-alpina-admin_alpina-media/'+save
    foto['img'] = ruta
    connection.guardar_url_original(db, foto['id'],ruta)

def save_answer(db, respuesta):
    guardar_imagenes(db, respuesta)
    imagenes = respuesta['imagenes']
    return imagenes

def session_id(db):
    id = create_session()
    while not connection.existe_session(db, id):
        id = create_session()

    return id


def create_session():
    session_id = str(uuid.uuid4())
    return session_id.replace("-","")

def time_now():
    dateti = datetime.datetime.now()
    bogota = pytz.timezone('America/Bogota')

    with_timezone = bogota.localize(dateti)
    
    return with_timezone

def correo_falla_servidor(error, session_id, ambiente, direccion):
    emails=['j.jaramillo@lucro-app.com','c.hernandez@lucro-app.com','a.ramirez@lucro-app.com']
    tipo = 'ROJA' if ambiente == 'AWS-2' else 'AMARILLA'
    subject = f'[ALERTA {tipo}] - El servidor de Reconocimiento de Alpina ha reportado un error en {ambiente}'
    time = time_now().strftime("%m/%d/%Y, %H:%M:%S")
    message = f"""
    Se ha presentado el siguiente error en el servidor:
    <br>
    <b>Ambiente:</b> {ambiente}.<br>
    <b>Ambiente:</b> {direccion}.<br>
    <b>Id de Session:</b> {session_id}.<br>
    <b>Fecha del error:</b> {time}.<br>
    <b>Información:</b> {error}.<br>
    <br>
    Por favor verificar si los datos son correctos.
    """
    mail = Mail()
    mail.send(emails, subject, message)

def debug_user(method:str, endpoint:str, entrada, salida, usuario: str, session_id:str =None):
    today = time_now()
    today = today.strftime("%d-%m-%Y %H:%S")
    info = f"{method};;{endpoint};;{today};;{usuario};;{session_id};;{entrada};;{salida}"
    print(info)

def change_variables(data: list):
    for info in data:
        cuadro = info['bounding_box']
        cuadro["x_min"] = float(cuadro["x_min"])
        cuadro["y_min"] = float(cuadro["y_min"])
        cuadro["x_max"] = float(cuadro["x_max"])
        cuadro["y_max"] = float(cuadro["y_max"])

        cuadro['height'] = cuadro["y_max"] - cuadro["y_min"] 
        cuadro['width'] = cuadro["x_max"] - cuadro["x_min"]

    return data