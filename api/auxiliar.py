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
import json

settings = configs.get_db_settings()
bucket = configs.get_storage()
trans_recon_names = {
    'brand': 'Marca',
    'train_name': 'Nombre',
}
with open(settings.MC_CONFIGS, 'r') as file:
    new_configs = json.load(file)

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
    

def marcar_imagen(id,
                  username,
                  original,
                  data,
                  session_id=None,
                  from_url=True,
                  type_service='general',
                  info=True):
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

    if info:
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
    else:
        result = image

    # convert to jpeg and save in variable
    cv2.imwrite(path,result)
    if from_url:
        #Salva en el storage de Google
        save = f"mark_images/{type_service}/{username}/{session_id}/{id}.jpg"
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

def correo_falla_servidor(error, session_id, ambiente, direccion, tipo):
    emails=[x['email'] for x in new_configs['correos']]
    subject = f'[ALERTA {tipo}] - El servidor de Reconocimiento de Alpina ha reportado un error en {ambiente} (Integración)'
    time = time_now().strftime("%m/%d/%Y, %H:%M:%S")
    message = f"""
    Se ha presentado el siguiente error en el servidor:
    <br>
    <b>Ambiente:</b> {ambiente}.<br>
    <b>Dirección:</b> {direccion}.<br>
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


def send_image(path, image):
    res1 = requests.post(path, files=image, verify=False)
    if res1.status_code == 200:
        prod = res1.json().get("results", list())
        if prod:
            data = prod[0]["Detections"]
            size = prod[0]["Metadata"]["size"]
            data = change_variables(data)
            return data, size.get('height', None), size.get('width', None)
    else:
        return list(), None, None

def make_request(imagen, username, id, session_id = None, from_url=True, db=None):
    if from_url:
        image = [('image', (requests.get(imagen).content))]
    else:
        image = [('image', (imagen))]
    
    error = None
    servers = new_configs['servers']
    complete_data = list()
    data = dict()
    for server in servers:
        try:
            ambiente = "GPU"
            path = server['main']
            type_service = server['type']
            data[type_service], height, width = send_image(path, image)
            info = {
                "data": data[type_service],
                "session_id": session_id,
                "type_recon": type_service,
            }
            connection.actualizar_subconsultas(db, id, type_service, info)
            db.commit()
            marcada = marcar_imagen(id,
                                    username,
                                    imagen,
                                    info['data'],
                                    session_id,
                                    from_url,
                                    info=True,
                                    type_service=type_service)
            info = {
                "mark_url": marcada,
            }
            connection.actualizar_subconsultas(db, id, type_service, info)
            db.commit()
            complete_data += data[type_service]

        except Exception as e:
            print("Primer error: " + str(e))
            if from_url:
                correo_falla_servidor(str(e), id, ambiente, path, "AMARILLA")

            try:
                ambiente = "CPU"
                path = server['backup']
                type_service = server['type']
                data[type_service], height, width = send_image(path, image)
                info = {
                    "data": data[type_service],
                    "session_id": session_id,
                    "type_recon": type_service,
                }
                connection.actualizar_subconsultas(db, id, type_service, info)
                db.commit()
                marcada = marcar_imagen(id,
                                        username,
                                        imagen,
                                        info['data'],
                                        session_id,
                                        from_url,
                                        info=True,
                                        type_service=type_service)
                info = {
                    "mark_url": marcada,
                }
                connection.actualizar_subconsultas(db, id, type_service, info)
                db.commit()
                complete_data += data[type_service]
                
            except Exception as e:
                print(f"Error en imagen {id}: " + str(e))
                error = str(e)
                if from_url:
                    correo_falla_servidor(str(e), id, ambiente, path, "ROJA")
                
    filtered_data = complete_data
    material_pop = [x for x in complete_data if x['obj_name']['Categoria'] == 'PoP']
    for m_pop in material_pop:
        bbox = m_pop['bounding_box']
        filtered_data = get_filtered_products(filtered_data, bbox, inside=False, expansion_factor=-0.01)

    marcada = marcar_imagen(id, username, imagen, filtered_data, session_id, from_url, info=False)
    trans = get_raw_recognitions(db, filtered_data, id, from_url)
    connection.actualizar_imagen(db, id, filtered_data, marcada, error, ambiente)
    connection.actualizar_size(db, id, height, width)
    return filtered_data, trans, marcada, error

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


def get_filtered_products(products, bounding_box, expansion_factor=0, inside=True):
    inside_products = []
    outside_products = []
    xmin = bounding_box['x_min']
    xmax = bounding_box['x_max']
    ymin = bounding_box['y_min']
    ymax = bounding_box['y_max']

    # Calculate the expansion amount based on the provided factor
    x_expansion = (xmax - xmin) * expansion_factor
    y_expansion = (ymax - ymin) * expansion_factor

    # Expand the bounding box by the expansion amount
    xmin -= x_expansion
    xmax += x_expansion
    ymin -= y_expansion
    ymax += y_expansion

    for product in products:
        product_box = product['bounding_box']
        x_min = product_box['x_min'] >= xmin
        x_max = product_box['x_max'] <= xmax
        y_min = product_box['y_min'] >= ymin
        y_max = product_box['y_max'] <= ymax
        is_inside = x_min and x_max and y_min and y_max
        if is_inside:
            inside_products.append(product)
        else:
            outside_products.append(product)

    return inside_products if inside else outside_products
