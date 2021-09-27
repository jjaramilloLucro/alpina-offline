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

version = "1.3.0"

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
    cliente = access.authenticate(form_data.username, form_data.password)
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
    return [x for x in desafios if x['document_id'] in user['desafios']]

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
    return auxiliar.identificar_producto(resp['img'], resp['id'])

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
    lat: Optional[str] = Form(None), lon: Optional[str] = Form(None)
):
    imgs = imgs if imgs else list()
    resp = resp if resp else list()
    respuestas = {'id_preg':id_preg, 'imgs': [file.file.read() for file in imgs], 'resp':resp}
    #respuestas = {'id_preg':id_preg, 'imgs': [file.filename for file in imgs]}
    body =  {
        "uid": uid,
        "document_id": document_id,
        "session_id": session_id,
        "respuestas": respuestas,
        "lat": lat,
        "lon": lon,
        "created_at": auxiliar.time_now()
    }
    
    imagenes = auxiliar.save_answer(body)
    background_tasks.add_task(auxiliar.actualizar_imagenes, imagenes = imagenes)
    return body

@app.post("/infaltables", tags=["Desafios"])
async def set_infaltables(challenge_id: str, productos: List[str], token: str = Depends(oauth2_scheme)):
    
    connection.escribir_faltantes(challenge_id,productos)
    return {"challenge_id":challenge_id, "productos":productos}

@app.get("/", tags=["Usuarios"])
async def get_session_id( token: str = Depends(oauth2_scheme)):
    return auxiliar.session_id()

@app.get("/infaltables", tags=["Desafios"])
async def get_infaltables(session_id: str, token: str = Depends(oauth2_scheme)):
    respuesta = connection.get_respuestas(session_id)
    infaltables = connection.get_faltantes(respuesta['document_id'])
    reconocio, termino = connection.get_productos(session_id)
    faltantes = list(set(infaltables) - set(reconocio))
    return {"termino":termino, "faltantes": faltantes}

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