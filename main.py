from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from api import connection, access, schemas, auxiliar
import models, time
from database import SessionLocal, engine

tags_metadata = [
    {
        "name": "Ping",
        "description": "Make ping.",
    },
    {
        "name": "Users",
        "description": "Users services.",
    },
    {
        "name": "Challenges",
        "description": "Challenges services.",
    },
    {
        "name": "Essentials",
        "description": "Essentials services.",
    },
    {
        "name": "Visits",
        "description": "Visits services.",
    },
    {
        "name": "Comments",
        "description": "Comments services.",
    },
    {
        "name": "CSV Files",
        "description": "Upload data from CSV files.",
    },
]

version = "4.3.2"

######## Configuración de la app
app = FastAPI(title="API Alpina Offline",
    description="API for Alpina offline app.",
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
@app.post("/token", tags=["Users"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    username = form_data.username
    username = username.replace(" ","")
    cliente = access.authenticate(db, username, form_data.password)
    if not cliente or not cliente['isActive']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = access.create_access_token(
        data={"sub": cliente["username"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/user", tags=["Users"], response_model=schemas.User)
def create_user(resp: schemas.RegisterUser, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = resp.__dict__
    user['password'] = access.get_password_hash(user['password'])
    user = connection.set_user(db, user)
    return user

@app.get("/challenges", tags=["Challenges"])
def get_challenges(username:str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = connection.get_user(db, username)
    tiendas = connection.get_tienda_user(db, user['username'])
    dia = auxiliar.time_now().weekday()
    puntos = [{"key":x['client_id'],"value":x['name']} for x in tiendas if dia in x['day_route']]
    grupo = connection.get_grupo(db, user['group'])
    challenges = [{"group_id":g.id, "real_name":g.name,'challenge':connection.get_challenge(db, g.challenge)} for g in grupo]
    id_tienda = 0
    for i in range(len(challenges)):
        challenges[i]['challenge']['document_id'] = str(challenges[i]['group_id']) + '__' + str(challenges[i]['challenge']['challenge_id'])
        challenges[i]['challenge']['name'] = challenges[i]['real_name']
        for pregunta in challenges[i]['challenge']['tasks']:
            if pregunta['store']:
                id_tienda = pregunta['id']
                pregunta['options'] = puntos

        for punto in tiendas:
            for adicional in punto['add_exhibition']:
                ad = {
                    "title": adicional,
                    "body": f"Tomale una foto a la Exhibición adicional de {adicional}",
                    "ref_img": "",
                    "id": len(challenges[i]['challenge']['tasks']),
                    "type": "Foto",
                    "required": True,
                    "store": False,
                    "options": [],
                    "condition": {
                        "id": id_tienda,
                        "options": []
                    }
                }
                challenges[i]['challenge']['tasks'].append(ad)
    
    return [x['challenge'] for x in challenges]

@app.get("/stores", tags=["Challenges"])
def get_stores_challenges(username:str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = connection.get_user(db, username)
    tiendas = connection.get_tienda_user(db, user['username'])
    dia = auxiliar.time_now().weekday()
    
    puntos=list()
    for i, tienda in enumerate(tiendas):
        if dia in tienda["day_route"]:
            grupo = connection.get_grupo(db, tienda['group'].split(","))
            challenges = [{"group_id":g.id, "real_name":g.name,'challenge':connection.get_challenge(db, g.challenge)} for g in grupo]
            for challenge in challenges:
                tasks = [x for x in challenge['challenge']['tasks'] if not x['store']]
                for adicional in tienda['add_exhibition']:
                    ad = {
                        "title": adicional,
                        "body": f"Tomale una foto a la Exhibición adicional de {adicional}",
                        "ref_img": "",
                        "id": len(tasks),
                        "type": "Foto",
                        "required": True,
                        "store": False,
                        "options": [],
                        "condition": {}
                    }
                    tasks.append(ad)

                puntos.append({
                    "document_id":str(challenge['group_id']) + '__' + str(challenge['challenge']['challenge_id']) + '__' + str(dia) + '__' + str(i) ,
                    "store_key":tienda['client_id'],
                    "store_name":tienda['name'],
                    "store_lat":tienda['lat'],
                    "store_lon":tienda['lon'],
                    "channel":tienda['channel'],
                    "group":challenge['real_name'],
                    "tasks":tasks
                })
    
    return puntos

@app.get("/challenges/{id}", tags=["Challenges"])
def get_challenges(id:str, token: str = Depends(oauth2_scheme),  db: Session = Depends(get_db)):
    return connection.get_challenge(db, id)

@app.post("/essentials", tags=["Essentials"] )
def set_essentials(group_id: str, productos: List[dict], token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    faltantes = {"group_id":group_id,"prods":productos}
    return connection.set_infaltables(db, faltantes)

@app.post("/prueba")
async def prueba_maquina(resp: schemas.Prueba, db: Session = Depends(get_db) ):
    resp = resp.__dict__
    return auxiliar.identificar_producto(db, resp['img'], resp['id'], resp['session_id'])

@app.get("/decode")
async def decode_imagen(url: str ):
    return auxiliar.decode(url)

@app.get("/code")
async def code(cod:str):
    return access.get_password_hash(cod)

@app.post("/answer", tags=["Visits"])
async def set_answer(answer: schemas.RegisterAnswer, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme) ):
    answer = answer.dict()
    respuestas = connection.get_respuestas(db, answer['session_id'])
    existe = [x.split('-')[1] for resp in respuestas for x in resp['imgs']]
    answer['imgs'] = list(set(answer['imgs'])-set(existe))
    answer['imgs'] = [answer['session_id']+'-'+x for x in answer['imgs']]
    #answer['resp'] = answer['resp'][0] if answer['resp'] else ""
    #answer['store'] = answer['resp'] != ""
    answer["created_at"]= auxiliar.time_now()
    return connection.guardar_resultados(db, answer)

@app.post("/answer/{session_id}", tags=["Visits"])
async def send_image(session_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme), imgs: Optional[List[UploadFile]] = File(None)
):
    imgs = imgs if imgs else list()
    ids = [file.filename.split(".")[0] for file in imgs]
    body =  {
            "session_id": session_id,
            "created_at": auxiliar.time_now(),
            "imagenes": ids
        }
    respuestas = connection.get_images(db, session_id)
    existe = [x['resp_id'].split('-')[1]for x in respuestas]
    falt = list(set(ids)-set(existe))
    if falt:
        imgs = [file for file in imgs if file.filename.split(".")[0] in falt]
        body['imagenes'] =  [{'id': session_id+'-'+file.filename.split(".")[0], 'img': file.file.read()} for file in imgs]
        imagenes = auxiliar.save_answer(db, body)
        background_tasks.add_task(auxiliar.actualizar_imagenes, db=db, imagenes = imagenes, session_id=session_id)
    
    del body['imagenes']
    return falt

@app.get("/", tags=["Users"])
async def get_session_id( token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return auxiliar.session_id(db)

@app.get("/missings", tags=["Essentials"])
def get_missings(session_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    faltantes = connection.get_faltantes(db, session_id)
    if faltantes:
        return {"finish":True, "sync":True, "missings":faltantes['products']}

    promises = connection.get_promises_images(db, session_id)
    serv = connection.get_images(db, session_id)
    serv = [x['resp_id'] for x in serv]
    if not set(promises) == set(serv):
        return {"finish":True, "sync":False, "missings":list()}
    
    else:
        final, faltantes = connection.calculate_faltantes(db, session_id)
        if final:
            connection.set_faltantes(db, session_id, faltantes)
        return {"finish":final, "sync":True, "missings":faltantes}

@app.get("/image", tags=["Essentials"])
async def get_image(session_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    respuestas = connection.get_respuestas(db, session_id)
    imgs = connection.get_images(db, session_id)
    imgs = {x['resp_id']:x['data'] for x in imgs}

    imagenes = [{"id_preg":resp['id_task'],"imgs":x, "data":imgs[x]} for resp in respuestas for x in resp['imgs']]
    return imagenes

@app.post("/challenge", tags=["Challenges"])
def set_challenge( challenge: schemas.RegisterChallenge, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    challenge = challenge.__dict__
    challenge['tasks'] = [x.__dict__ for x in challenge['tasks']]
    return connection.set_challenge(db, challenge)

@app.get("/sync/{session_id}", tags=["Visits"])
def get_ids_by_session( session_id: str, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    respuestas = connection.get_images(db, session_id)

    imagenes = [x['resp_id'] for x in respuestas]

    return imagenes

@app.post("/files/stores", tags=["CSV Files"])
def upload_stores( file: UploadFile = File(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    return connection.upload_stores(db, file.file)

@app.post("/files/users", tags=["CSV Files"])
def upload_users( file: UploadFile = File(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    return connection.upload_users(db, file.file)

@app.get("/ping", tags=["Ping"])
def ping():
    return True

@app.get("/sync", tags=["Ping"])
def sync_day_route():
    return auxiliar.time_now().weekday()

@app.put("/version/{username}", tags=["Users"])
def user_version(username: str, version: str,db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    return connection.set_version(db,username,version)

@app.get("/deco")
def decode_token(token: str = Depends(oauth2_scheme)):
    return access.decode(token)

@app.post("/comment", tags=["Comments"])
def set_comment( store: schemas.RegisterComment, db: Session = Depends(get_db)):
    return connection.set_comment(db, store.dict())
