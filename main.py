from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

import connection, access, schemas, auxiliar
import datetime

tags_metadata = [
    {
        "name": "Usuarios",
        "description": "Servicios de Usuarios.",
    },
    {
        "name": "Desafios",
        "description": "Servicios de Desafios.",
    },
    {
        "name": "Respuestas",
        "description": "Servicios de Respuestas.",
    },
]

version = "2.1.2"

######## Configuración de la app
app = FastAPI(title="API Offline Alpina",
    description="API de manejo de información para la aplicación offline.",
    version=version,
    openapi_tags=tags_metadata
    )

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token", tags=["Usuarios"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    username = username.replace(" ","")
    cliente = access.authenticate(username, form_data.password)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = access.create_access_token(
        data={"sub": cliente["username"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/desafios", tags=["Desafios"])
async def get_desafios(usuario:str, token: str = Depends(oauth2_scheme)):
    user = connection.getUser(usuario)
    desafios = connection.getAllChallenges()
    desafios = [x for x in desafios if x['document_id'] in user['desafios']]
    for i in range(len(desafios)):
        for pregunta in desafios[i]['tasks']:
            if 'tienda' in pregunta:
                pregunta['options'] = user['puntos']
            if 'zona' in pregunta:
                pregunta['options'] = user['zonas']
    
    return desafios

@app.get("/desafios/{id}", tags=["Desafios"])
async def get_desafios(id:str, token: str = Depends(oauth2_scheme)):
    return connection.getChallenge(id)

@app.post("/desafios", tags=["Desafios"], response_model=schemas.Desafio)
async def set_desafios(resp: schemas.RegistroDesafio, token: str = Depends(oauth2_scheme)):
    respuesta = resp.__dict__
    respuesta['tasks'] = [i.__dict__ for i in respuesta['tasks']]
    respuesta['expire'] = datetime.datetime.strptime('Oct 31 2021', '%b %d %Y')
    connection.escribir_desafio(respuesta)
    return respuesta

@app.post("/prueba")
async def prueba_maquina(resp: schemas.Prueba ):
    resp = resp.__dict__
    return auxiliar.identificar_producto(resp['img'], resp['id'], resp['session_id'])

@app.get("/decode")
async def decode_imagen(url: str ):
    
    return auxiliar.decode(url)

@app.get("/codificar")
async def codificar(cod:str):
    return access.get_password_hash(cod)


@app.post("/registrar", tags=["Respuestas"])
async def registrar_batch(background_tasks: BackgroundTasks, resp: schemas.RegistroRespuesta , token: str = Depends(oauth2_scheme), ):
    respuesta = resp.__dict__
    respuesta['respuestas'] = [i.__dict__ for i in respuesta['respuestas']]
    respuesta['datetime'] = datetime.datetime.now()
    imagenes = auxiliar.save_answer(respuesta)

    background_tasks.add_task(auxiliar.actualizar_imagenes, imagenes = imagenes)

    return respuesta

@app.post("/respuesta", tags=["Respuestas"])
async def registrar_respuesta(background_tasks: BackgroundTasks, session_id: str = Form(...), resp: Optional[List[str]] = Form(None),
    imgs: Optional[List[UploadFile]] = File(None), token: str = Depends(oauth2_scheme), document_id: str = Form(...), uid: str = Form(...), id_preg: int = Form(...),
    lat: Optional[str] = Form(None), lon: Optional[str] = Form(None), tienda:  Form(Optional[bool]) = False
):
    imgs = imgs if imgs else list()
    resp = resp if resp else list()
    respuestas = {'id_preg':id_preg, 
        'img_ids': [file.filename.split(".")[0] for file in imgs],
        'imgs': [file.file.read() for file in imgs], 
        'resp':resp,
        "lat": lat,
        "lon": lon,
    }

    body =  {
        "uid": uid,
        "document_id": document_id,
        "session_id": session_id,
        "respuestas": respuestas,
        "created_at": auxiliar.time_now()
    }
    
    if tienda:
        body["tienda"] = resp[0]
    imagenes = auxiliar.save_answer(body)
    background_tasks.add_task(auxiliar.actualizar_imagenes, imagenes = imagenes, session_id=session_id)
    return body

@app.post("/infaltables", tags=["Desafios"])
async def set_infaltables(challenge_id: str, productos: List[str], token: str = Depends(oauth2_scheme)):
    
    connection.escribir_faltantes(challenge_id,productos)
    return {"challenge_id":challenge_id, "productos":productos}

@app.get("/", tags=["Usuarios"])
async def get_session_id( token: str = Depends(oauth2_scheme)):
    return auxiliar.session_id()

@app.get("/infaltables", tags=["Desafios"])
async def get_infaltables(background_tasks: BackgroundTasks, session_id: str, token: str = Depends(oauth2_scheme)):
    respuesta = connection.get_respuestas(session_id)
    final = connection.escribir_faltantes(session_id,respuesta['document_id'])
    if final['termino'] and not final['valido']:
        print("Empezando a validar")
        connection.validar_imagenes(session_id=session_id)
    return {"termino":final['valido'], "faltantes": final['faltantes']}

@app.get("/marcacion", tags=["Desafios"])
async def get_imagen_marcada(session_id: str, token: str = Depends(oauth2_scheme)):
    respuesta = connection.get_respuestas(session_id)

    imagenes = [{"id_preg":resp['id_preg'],"imgs":resp['imgs']} for resp in respuesta['respuestas']]

    for i in range(len(imagenes)):
        marcaciones = list()
        for x in imagenes[i]['imgs']:
            marc = connection.get_imagen_marcada(x)
            if 'data' in marc:
                marcaciones.append(marc['data'])
            else:
                marcaciones.append(list())
        
        imagenes[i]['data'] = marcaciones

    return imagenes

@app.post("/usuario", tags=["Usuarios"], response_model=schemas.Usuario )
async def create_user(resp: schemas.RegistroUsuario, token: str = Depends(oauth2_scheme)):
    user = resp.__dict__
    user['password'] = access.get_password_hash(user['password'])
    connection.escribir_usuario(user)
    return user

@app.get("/getURL/{session_id}" )
async def get_url(session_id: str):
    
    return connection.get_urls(session_id)

@app.get("/sincronizar", tags=["Respuestas"])
async def sincronizar(session_id: str, token: str = Depends(oauth2_scheme)):
    return connection.get_respuestas(session_id)

@app.get("/retry", tags=["Respuestas"])
async def intentar_de_nuevo(session_id: str, token: str = Depends(oauth2_scheme)):
    resp,valid = connection.get_images_error(session_id)
    valido, error = list(), list()
    for imagen in resp:
        try:
            auxiliar.identificar_producto(imagen['url_original'],imagen['document_id'],session_id)
            valido.append({"document_id":imagen['document_id'],"valid":True})
        except Exception as e:
            error.append({"document_id":imagen['document_id'],"error":str(e)})
    return {"termino":valid,"validas":valido, "errores":error}