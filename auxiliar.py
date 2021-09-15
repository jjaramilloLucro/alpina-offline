import os, json, copy, requests, base64, io, time
import configs, connection
from threading import Thread

settings = configs.get_db_settings()


def identificar_producto(imagen, id):
    time.sleep(10)

    '''
    
    img = base64.b64encode(requests.get(imagen).content)
    post_data = {
        "image": img,
        "service": settings.SERVICE,        
        "thresh": settings.THRESHOLD,
        "get_img_flg": settings.IMG_FLAG}

    try:
        res1 = requests.post("http://retailappml.eastus.cloudapp.azure.com:8081/detect", json=post_data)
        prod = json.loads(res1.text)
        if 'resultlist' in prod:
            data = prod['resultlist']
        else:
             data = "No hubo reconocimiento"

        connection.actualizar_imagen(id, data)
            
    except Exception as e:
        connection.actualizar_imagen(id, e)
    '''    
    connection.actualizar_imagen(id, 'Actualizamos!!!')

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

def upload_image(foto, respuesta):
    '''
    img_data = base64.b64decode(foto['img'])
    path = os.path.join('img',f"{foto['id']}.png")
    img = Image.open(io.BytesIO(img_data))
    img.save(path, 'png')

    client = storage.Client()
    bucket = client.get_bucket(settings.GS_BUCKET_NAME)
    save = f"resp_images/{respuesta['uid']}/{respuesta['document_id']}/{foto['id']}.png"
    object_name_in_gcs_bucket = bucket.blob(save)

    object_name_in_gcs_bucket.upload_from_filename(path)
    os.remove(path)
    '''
    save = f"resp_images/{respuesta['uid']}/{respuesta['document_id']}/{foto['id']}.png"

    foto['img'] = 'https://storage.googleapis.com/lucro-alpina-admin_alpina-media/'+save


def save_answer(respuesta):
    id = connection.documento_temporal()
    connection.guardarResultadosImagen(respuesta, id)
    guardar_imagenes(respuesta)
    imagenes = respuesta['imagenes']
    del respuesta['imagenes']
    connection.guardarResultados(respuesta,id)
    return imagenes