import os, requests, base64
import configs
from api import connection
from threading import Thread
import cv2
import numpy as np
import pytz, datetime, time
import urllib.request
from api.correo import Mail
import uuid
from sqlalchemy.orm import Session
from database import SessionLocal


settings = configs.get_db_settings()
bucket = configs.get_storage()
trans_recon_names = {
    'brand': 'Marca',
    'train_name': 'Nombre',
}


def decode(url):
    img = base64.b64encode(requests.get(url).content)
    return img.decode('utf-8')

def actualizar_imagenes(imagenes, session_id, username):
    threads = list()
    for foto in imagenes:
        db = SessionLocal()
        t = Thread(target=identificar_producto, args=(db, foto['img'],foto['id'],session_id, username))
        info = {
            "session": db,
            "thread": t 
        }
        threads.append(info)

    [thread["thread"].start() for thread in threads]

    for thread in threads:
        thread['thread'].join()
        try:
            thread['session'].commit()
        except:
            thread['session'].rollback()
        finally:
            thread['session'].close()

def identificar_producto(db, imagen, id, session_id, username):
    resp = make_request(imagen, username, id, session_id=session_id, from_url=True, db=db)
    try:
        db.commit()
    except:
        db.rollback()
    return resp
    

def marcar_imagen(id, username, original, data, session_id=None, from_url=True):
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
    if from_url:
        url_response = urllib.request.urlopen(original) #Descarga la imagen del link
        image = cv2.imdecode(np.array(bytearray(url_response.read()), dtype=np.uint8), -1) #Lee la imagen
    else:
        image = cv2.imdecode(np.array(bytearray(original), dtype=np.uint8), -1)

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
    if from_url:
        #Salva en el storage de Google
        save = f"mark_images/{username}/{session_id}/{id}.jpg"
        object_name_in_gcs_bucket = bucket.blob(save)
        object_name_in_gcs_bucket.upload_from_filename(path)
        
        return 'https://storage.googleapis.com/lucro-alpina-admin_alpina-media/'+save
    else:
        return path

def guardar_imagenes(db: Session, respuesta, username):
    threads = list()
    for foto in respuesta['imagenes']:
        t = Thread(target=upload_image, args=(foto, respuesta, db, username))
        threads.append(t)

    [threads[i].start() for i in range(len(threads))]
    [threads[i].join() for i in range(len(threads))]
    try:
        db.commit()
    except:
        db.rollback()


def upload_image(foto, respuesta, db, username):
    img_data = foto['img']
    path = os.path.join('img',f"{foto['id']}.jpg")

    with open(path, 'wb') as handler:
        handler.write(img_data)

    save = f"original_images/{username}/{respuesta['session_id']}/{foto['id']}.jpg"
    object_name_in_gcs_bucket = bucket.blob(save)

    object_name_in_gcs_bucket.upload_from_filename(path)

    ruta = 'https://storage.googleapis.com/lucro-alpina-admin_alpina-media/'+save
    foto['img'] = ruta
    connection.guardar_url_original(db, foto['id'],ruta)

def save_answer(db, respuesta, username):
    guardar_imagenes(db, respuesta, username)
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
    emails=['j.jaramillo@lucro-app.com',
            #'c.hernandez@lucro-app.com',
            #'a.ramirez@lucro-app.com',
            'f.morales@lucro-app.com',
            'c.moreno@lucro-app.com',
            ]
    tipo = 'ROJA' if ambiente == 'GCP-2' else 'AMARILLA'
    subject = f'[ALERTA {tipo}] - El servidor de Reconocimiento de Alpina ha reportado un error en {ambiente} (Integración)'
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
        cuadro["x_min"] = float(cuadro["xmin"])
        cuadro["y_min"] = float(cuadro["ymin"])
        cuadro["x_max"] = float(cuadro["xmax"])
        cuadro["y_max"] = float(cuadro["ymax"])

        cuadro['height'] = cuadro["y_max"] - cuadro["y_min"] 
        cuadro['width'] = cuadro["x_max"] - cuadro["x_min"]

    return data

def test_image_service(file, db, username):
    bytes_file = file.file.read()
    return make_request(bytes_file, username, "prueba", from_url=False, db=db)


def make_request(imagen, username, id, session_id = None, from_url=True, db=None):
    if from_url:
        image = [('image', (requests.get(imagen).content))]
    else:
        image = [('image', (imagen))]
    try:
        print("Primer Intento")
        path = f"http://{settings.MC_SERVER}"
        if settings.MC_PORT:
            path += f":{settings.MC_PORT}"

        path += f"/{settings.MC_PATH}/"
        res1 = requests.post(path, files=image, verify=False)
        if res1.status_code == 200:
            prod = res1.json().get("results", list())
            if prod:
                data = prod[0]["Detections"]
                data = change_variables(data)
                marcada = marcar_imagen(id, username, imagen, data, session_id, from_url)
                error = None
                
                trans = get_raw_recognitions(db, data, id, from_url)
            else:
                data = list()
                error = configs.ERROR_MAQUINA
                marcada = None
            if from_url:
                connection.actualizar_imagen(db, id, data, marcada, error, "AWS-1")
            return data, trans, marcada, error
        else:
            connection.actualizar_imagen(db, id, list(), None, "Imagen Corrupta", "AWS-1")
            print("Imagen Corrupta", id)
            return list(), list(), None, "Imagen Corrupta"
    except Exception as e:
        print("Primer error: " + str(e))
        if from_url:
            correo_falla_servidor(str(e),id,"GCP-1",path)

    try:
        print("Segundo intento AWS")
        if settings.MC_SERVER2:
            path = f"http://{settings.MC_SERVER2}"
        else:
            path = f"http://{settings.MC_SERVER}"

        if settings.MC_PORT:
            path += f":{settings.MC_PORT}"

        path += f"/{settings.MC_PATH}/"
        res1 = requests.post(path, files=image, verify=False)
        if res1.status_code == 200:
            prod = res1.json().get("results", list())
            if prod:
                data = prod[0]["Detections"]
                data = change_variables(data)
                marcada = marcar_imagen(id, username, imagen, data, session_id, from_url)
                error = None
                
                trans = get_raw_recognitions(db, data, id, from_url)
            else:
                data = list()
                error = configs.ERROR_MAQUINA
                marcada = None
            if from_url:
                connection.actualizar_imagen(db, id, data, marcada, error, "GCP-2")
            return data, trans, marcada, error
        else:
            connection.actualizar_imagen(db, id, list(), None, str(e), "AWS-2")
            return list(), list(), None, str(e)
    except Exception as e:
        print(f"Error en imagen {id}: " + str(e))
        if from_url:
            connection.actualizar_imagen(db, id, list(), None, str(e), "AWS-2")
            correo_falla_servidor(str(e),id,"AWS-2",path)
        return list(), list(), None, str(e)
    

def get_raw_recognitions(db, resp, img_id, from_url):
    new_resp = list()
    list_data = list()
    if not resp:
        return new_resp
    for data in resp:
        new_data = dict()
        name_product = data['obj_name']['Nombre'] if isinstance(data['obj_name'], dict) else data['obj_name']
        product = connection.get_product_by_train_name(db, name_product)
        if product:
            temp_data = {
                    "resp_id": img_id,
                    "train_product_id": product.train_product_id,
                    "score": data['score'],
                    "bounding_box": data['bounding_box']
                }
            list_data.append(temp_data)
                
            new_data['sku'] = product.sku if product else None
            new_data['name'] = product.display_name if product else None
            new_data['bounding_box'] = data['bounding_box']
        
            new_resp.append(new_data)

    if from_url:
        connection.set_bulk_recon(db, list_data)
        db.commit()

    return new_resp


def calculate_general_missings(db, session_id):
    visit = connection.get_store_by_session_id(db, session_id)
    reconocidos = connection.get_reconocidos_complete(db, session_id)

    essentials = connection.get_essentials_general(db, visit.store)

    dict_evaluate = dict()
    for row in essentials:
        row = row._asdict()
        type_prod = trans_recon_names.get(row['type_of_prod'], row['type_of_prod'])
        if type_prod not in dict_evaluate:
            dict_evaluate[type_prod] = list()
        dict_evaluate[type_prod].append(row[row['type_of_prod']])

    final_evaluate = {i:list(set(dict_evaluate[i])) for i in dict_evaluate}
    
    resp = list()
    for i in final_evaluate:
        if i == 'train_name':
            recons = connection.get_reconocidos(db, session_id)
            recons = connection.traducir_reconocidos(db, recons)
            recons = list(set(recons))
        else:
            recons = final_evaluate[i]

        for j in recons:
            resp_session = {
                "session_id": session_id,
                "evaluated": j
            }
            
            recon_obj = list(set([x[i] for x in reconocidos]))
            resp_session['exist'] = j in recon_obj
            resp.append(resp_session)

    resp = connection.set_missings_general(db, resp)

    return resp
