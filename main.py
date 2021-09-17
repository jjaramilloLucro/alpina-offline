from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks, File, UploadFile, Form

import connection, access, schemas, auxiliar
import datetime

tags_metadata = [
    {
        "name": "Modulo API",
        "description": "Servicios de API.",
    },
]

version = "1.2.1"

######## Configuración de la app
app = FastAPI(title="API Offline Alpina",
    description="API de manejo de información para la aplicación offline.",
    version=version,
    openapi_tags=tags_metadata
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
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

@app.get("/desafios", tags=["Modulo API"])
async def get_desafios(usuario:str, token: str = Depends(oauth2_scheme)):
    user = connection.getUser(usuario)
    desafios = connection.getAllChallenges()
    return [x for x in desafios if x['document_id'] in user['desafios']]

@app.get("/desafios/{id}", tags=["Modulo API"])
async def get_desafios(id:str, token: str = Depends(oauth2_scheme)):
    return connection.getChallenge(id)

@app.post("/desafios", tags=["Modulo API"], response_model=schemas.Desafio)
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

@app.get("/infaltables", tags=["Modulo API"])
async def get_infaltables(token: str = Depends(oauth2_scheme)):
    return connection.getAllInfaltables()

@app.post("/registrar", tags=["Modulo API"])
async def registrar_respuesta(background_tasks: BackgroundTasks, resp: schemas.RegistroRespuesta , token: str = Depends(oauth2_scheme), ):
    respuesta = resp.__dict__
    respuesta['respuestas'] = [i.__dict__ for i in respuesta['respuestas']]
    respuesta['datetime'] = datetime.datetime.now()
    imagenes = auxiliar.save_answer(respuesta)

    background_tasks.add_task(auxiliar.actualizar_imagenes, imagenes = imagenes)

    return respuesta

@app.post("/respuesta")
async def create_file(background_tasks: BackgroundTasks, session_id: Optional[str] = Form(None), resp: Optional[List[str]] = Form(None),
    imgs: Optional[List[UploadFile]] = File(None), token: str = Depends(oauth2_scheme), document_id: str = Form(...), uid: str = Form(...), id_preg: int = Form(...)
):
    imgs = imgs if imgs else list()
    resp = resp if resp else list()
    respuestas = {'id_preg':id_preg, 'imgs': [file.file.read() for file in imgs], 'resp':resp}
    #respuestas = {'id_preg':id_preg, 'imgs': [file.filename for file in imgs]}
    body =  {
        "uid": uid,
        "document_id": document_id,
        "session_id": session_id,
        "respuestas": respuestas
    }
    
    imagenes = auxiliar.save_answer(body)
    background_tasks.add_task(auxiliar.actualizar_imagenes, imagenes = imagenes)
    return body