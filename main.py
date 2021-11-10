from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sqlalchemy.sql.roles import ConstExprRole

from api import connection, access, schemas, auxiliar
import models
from database import SessionLocal, engine
import time

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
        "name": "Infaltables",
        "description": "Servicios de Infaltables.",
    },
    {
        "name": "Respuestas",
        "description": "Servicios de Respuestas.",
    },
]

version = "3.0.0"

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
models.Base.metadata.create_all(bind=engine)
# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

##### URLS
@app.post("/token", tags=["Usuarios"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    username = form_data.username
    username = username.replace(" ","")
    cliente = access.authenticate(db, username, form_data.password)
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

@app.post("/usuario", tags=["Usuarios"], response_model=schemas.Usuario)
def create_user(resp: schemas.RegistroUsuario, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = resp.__dict__
    user['password'] = access.get_password_hash(user['password'])
    connection.set_user(db, user)
    return user

@app.get("/desafios", tags=["Desafios"])
def get_desafios(usuario:str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = connection.get_user(db, usuario)
    tiendas = connection.get_tienda_user(db, user['username'])
    puntos = [x['nombre'] for x in tiendas]
    grupo = connection.get_grupo(db, user['group'])
    desafios = [connection.get_challenge(db, x) for x in grupo['challenges']]
    id_tienda = 0
    for i in range(len(desafios)):
        desafios[i]['document_id'] = str(grupo['id']) + '__' + str(desafios[i]['challenge_id'])
        for pregunta in desafios[i]['tasks']:
            if pregunta['store']:
                id_tienda = pregunta['id']
                pregunta['options'] = puntos

        for punto in tiendas:
            for adicional in punto['add_exhibition']:
                ad = {
                    "title": adicional,
                    "body": f"Tomale una foto a la Exhibición adicional de {adicional}",
                    "ref_img": "",
                    "id": len(desafios[i]['tasks']),
                    "type": "Foto",
                    "required": True,
                    "tienda": False,
                    "options": [],
                    "condition": {
                        "id": id_tienda,
                        "options": []
                    }
                }
                desafios[i]['tasks'].append(ad)
    
    return desafios

@app.get("/desafios/{id}", tags=["Desafios"])
def get_desafios(id:str, token: str = Depends(oauth2_scheme),  db: Session = Depends(get_db)):
    return connection.get_challenge(db, id)

@app.post("/infaltables", tags=["Infaltables"] )
def set_infaltables(id_grupo: str, productos: List[dict], token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    faltantes = {"group_id":id_grupo,"prods":productos}
    return connection.set_infaltables(db, faltantes)

@app.post("/prueba")
async def prueba_maquina(resp: schemas.Prueba, db: Session = Depends(get_db) ):
    resp = resp.__dict__
    return auxiliar.identificar_producto(db, resp['img'], resp['id'], resp['session_id'])

@app.get("/decode")
async def decode_imagen(url: str ):
    return auxiliar.decode(url)

@app.get("/codificar")
async def codificar(cod:str):
    return access.get_password_hash(cod)

@app.post("/respuesta", tags=["Respuestas"])
async def registrar_respuesta(background_tasks: BackgroundTasks, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme),
    session_id: str = Form(...), resp: Optional[List[str]] = Form(None), imgs: Optional[List[UploadFile]] = File(None), document_id: str = Form(...), 
    uid: str = Form(...), id_preg: int = Form(...), lat: Optional[str] = Form(None), lon: Optional[str] = Form(None), tienda: Optional[bool] =  Form(False)
):
    imgs = imgs if imgs else list()
    resp = resp[0] if resp else ""

    body =  {
        "uid": uid,
        "document_id": document_id,
        "session_id": session_id,
        'id_task':id_preg, 
        'img_ids': [file.filename.split(".")[0] for file in imgs],
        'imgs': [file.file.read() for file in imgs], 
        "lat": lat,
        "lon": lon,
        "store": tienda,
        "resp": resp,
        "created_at": auxiliar.time_now()
    }
    
    imagenes = auxiliar.save_answer(db, body)
    background_tasks.add_task(auxiliar.actualizar_imagenes, db=db, imagenes = imagenes, session_id=session_id)
    return body

@app.get("/", tags=["Usuarios"])
async def get_session_id( token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return auxiliar.session_id(db)

@app.get("/infaltables", tags=["Infaltables"])
def get_faltantes(session_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    faltantes = connection.get_faltantes(db, session_id)
    if faltantes:
        return {"finish":True, "faltantes":faltantes['products']}
    else:
        final, faltantes = connection.calculate_faltantes(db, session_id)
        connection.set_faltantes(db, session_id, faltantes)
        return {"finish":final, "faltantes":faltantes}

@app.get("/marcacion", tags=["Infaltables"])
async def get_imagen_marcada(session_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    respuestas = connection.get_respuestas(db, session_id)
    imgs = connection.get_images(db, session_id)
    imgs = {x['resp_id']:x['data'] for x in imgs}

    imagenes = [{"id_preg":resp['id_task'],"imgs":x, "data":imgs[x]} for resp in respuestas for x in resp['imgs']]
    return imagenes

@app.post("/desafio", tags=["Desafios"])
def crear_desafio( desafio: schemas.RegistroDesafio, db: Session = Depends(get_db)):
    desafio = desafio.__dict__
    desafio['tasks'] = [x.__dict__ for x in desafio['tasks']]
    return connection.set_challenge(db, desafio)