from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks, File, UploadFile

import connection, access, schemas, auxiliar
import datetime

tags_metadata = [
    {
        "name": "Modulo API",
        "description": "Servicios de API.",
    },
]

version = "1.2.0"

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