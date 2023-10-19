from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from api import connection, access, schemas, auxiliar
import models
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

version = "5.2.2"

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
    if username == form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password can't be same as username",
            headers={"WWW-Authenticate": "Bearer"},
        )
    cliente, debug = access.authenticate(db, username, form_data.password)
    if not cliente or not cliente['isActive']:
        if debug:
            entrada = {"username":form_data.username, "password": form_data.password}
            resp = {"detail":"Incorrect username or password", "status_code": "401"}
            auxiliar.debug_user("POST", "/token", entrada, resp, username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = access.create_access_token(
        data={"user": cliente["username"]}
    )
    resp = {"access_token": access_token, "token_type": "bearer"}
    if debug:
        entrada = {"username":form_data.username, "password": form_data.password}
        auxiliar.debug_user("POST", "/token", entrada, resp, username)
    return resp

@app.post("/user", tags=["Users"], response_model=schemas.User)
def create_user(resp: schemas.RegisterUser, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        user = resp.__dict__
        if user['username'] == user['password']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password can't be same as username"
            )
        user['password'] = access.get_password_hash(user['password'])
        u = connection.get_user(db, user['username'])
        if u:
            user = connection.update_user(db, user)
        else:
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

    resp = [x['challenge'] for x in challenges]

    if user.get("debug",False):
        auxiliar.debug_user("GET", "/challenges", {"username":username}, resp, user['username'])
    
    return resp

@app.get("/stores", tags=["Challenges"])
def get_stores_challenges(username:str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = connection.get_user(db, username)
    tiendas = connection.get_tienda_user(db, user['username'])
    dia = auxiliar.time_now().weekday()
    
    puntos=list()
    resp=list()
    for i, tienda in enumerate(tiendas):
        tienda = tienda._asdict()
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
                    "store_key":tienda['store_key'],
                    "store_name":tienda['name'],
                    "store_lat":tienda['lat'],
                    "store_lon":tienda['lon'],
                    "address":tienda['direction'],
                    "channel":tienda['channel'],
                    "group":challenge['real_name'],
                    "tasks":tasks
                })

                resp.append({
                    "document_id":str(challenge['group_id']) + '__' + str(challenge['challenge']['challenge_id']) + '__' + str(dia) + '__' + str(i) ,
                    "store_key":tienda['store_key'],
                    "store_name":tienda['name'],
                    "store_lat":tienda['lat'],
                    "store_lon":tienda['lon'],
                    "address":tienda['direction'],
                    "channel":tienda['channel'],
                    "group":challenge['real_name']
                })
    
    if user.get("debug",False):
        auxiliar.debug_user("GET", "/stores", {"username":username}, resp, user['username'])

    return puntos

@app.get("/challenges/{id}", tags=["Challenges"])
def get_challenges(id:str, token: str = Depends(oauth2_scheme),  db: Session = Depends(get_db)):
    username = access.decode_user(token)
    user = connection.get_user(db, username)
    resp = connection.get_challenge(db, id)
    if user.get("debug",False):
        auxiliar.debug_user("GET", f"/challenges/{id}", {"id":id}, resp, user['username'])
    return resp

@app.post("/essentials", tags=["Essentials"] )
def set_essentials(group_id: str, productos: List[dict], token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = access.decode_user(token)
    user = connection.get_user(db, username)
    faltantes = {"group_id":group_id,"prods":productos}
    resp = connection.set_infaltables(db, faltantes)
    if user.get("debug",False):
        auxiliar.debug_user("POST", "/essentials", {"group_id":group_id,"productos":productos}, resp, user['username'])
    
    return resp

@app.post("/prueba")
async def prueba_maquina(resp: schemas.Prueba, db: Session = Depends(get_db) ):
    resp = resp.__dict__
    a = auxiliar.identificar_producto(db, resp['img'], resp['id'], resp['session_id'])
    if resp['session_id'] != '0':
        db.commit()
    return a

@app.get("/decode")
async def decode_imagen(url: str ):
    return auxiliar.decode(url)

@app.get("/code")
async def code(cod:str):
    return access.get_password_hash(cod)

@app.post("/answer", tags=["Visits"])
async def set_answer(answer: schemas.RegisterAnswer, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme) ):
    answer = answer.__dict__
    respuestas = connection.get_respuestas(db, answer['session_id'])
    respuestas = [x._asdict() for x in respuestas]
    existe = [x.split('-')[-1] for resp in respuestas for x in resp['imgs']]
    answer['imgs'] = list(set(answer['imgs'])-set(existe))
    answer['imgs'] = [answer['session_id']+'-'+x for x in answer['imgs']]
    #answer['resp'] = answer['resp'][0] if answer['resp'] else ""
    #answer['store'] = answer['resp'] != ""
    answer["created_at"]= auxiliar.time_now()

    store = connection.get_tienda_sql(db, answer['store'])

    answer["store_key_analitica"] = store['store_key_analitica']

    resp = connection.guardar_resultados(db, answer)
    username = access.decode_user(token)
    user = connection.get_user(db, username)
    if user.get("debug",False):
        auxiliar.debug_user("POST", "/answer", answer, resp, user['username'], answer['session_id'])
    return resp

@app.post("/answer/{session_id}", tags=["Visits"])
async def send_image(session_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme), 
    imgs: List[UploadFile] = File(None)
):
    imgs = imgs if imgs else list()
    ids = [file.filename.split(".")[0] for file in imgs]
    body =  {
            "session_id": session_id,
            "created_at": auxiliar.time_now(),
            "imagenes": ids
        }
    respuestas = connection.get_images(db, session_id)
    existe = [x['resp_id'].split('-')[-1] for x in respuestas]
    falt = list(set(ids)-set(existe))
    if falt:
        imgs = [file for file in imgs if file.filename.split(".")[0] in falt]
        body['imagenes'] =  [{'id': session_id+'-'+file.filename.split(".")[0], 'img': file.file.read()} for file in imgs]
        imagenes = auxiliar.save_answer(db, body)
        background_tasks.add_task(auxiliar.actualizar_imagenes, db=db, imagenes = imagenes, session_id=session_id)
    
    del body['imagenes']
    resp = falt

    username = access.decode_user(token)
    user = connection.get_user(db, username)
    if user.get("debug",False):
        auxiliar.debug_user("POST", f"/answer/{session_id}", body, resp, user['username'], session_id)
    return resp


@app.get("/", tags=["Users"])
async def get_session_id( token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    resp = auxiliar.session_id(db)
    username = access.decode_user(token)
    user = connection.get_user(db, username)
    if user.get("debug",False):
        auxiliar.debug_user("GET", "/", "", resp, user['username'])
    return resp


@app.get("/missings", tags=["Essentials"])
def get_missings(session_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    faltantes = connection.get_faltantes(db, session_id)
    if faltantes:
        resp =  {"finish":True, "sync":True, "missings":faltantes['products']}
    else:
        promises = connection.get_promises_images(db, session_id)
        serv = connection.get_images(db, session_id)
        serv = [x['resp_id'] for x in serv]
        if not set(promises) == set(serv):
            resp = {"finish":True, "sync":False, "missings":list()}
        
        else:
            final, faltantes = connection.calculate_faltantes(db, session_id)
            if final:
                connection.set_faltantes(db, session_id, faltantes)
                #TODO: get_general_missings(db, session_id)
            resp = {"finish":final, "sync":True, "missings":faltantes}

    username = access.decode_user(token)
    user = connection.get_user(db, username)
    if user.get("debug",False):
        auxiliar.debug_user("GET", "/missings", {"session_id": session_id}, resp, user['username'], session_id)

    return resp


@app.delete("/missings", tags=["Essentials"])
def delete_missings(session_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    faltantes = connection.get_faltantes(db, session_id)
    if faltantes:
        a = connection.delete_faltantes(db, session_id)
        resp =  {"exist":True, "deleted":a}
    else:
        resp =  {"exist":False, "deleted":True}

    username = access.decode_user(token)
    user = connection.get_user(db, username)
    if user.get("debug",False):
        auxiliar.debug_user("DELETE", "/missings", {"session_id": session_id}, resp, user['username'], session_id)

    return resp

@app.get("/image", tags=["Essentials"])
async def get_image(session_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    respuestas = connection.get_respuestas(db, session_id)
    respuestas = [x._asdict() for x in respuestas]
    imgs = connection.get_images(db, session_id)
    imgs = {x['resp_id']:x['data'] for x in imgs}
    imagenes = [{"id_preg":resp['id_task'],"imgs":x, "data":imgs[x]} for resp in respuestas for x in resp['imgs']]

    username = access.decode_user(token)
    user = connection.get_user(db, username)
    if user.get("debug",False):
        auxiliar.debug_user("GET", "/image", {"session_id": session_id}, imagenes, user['username'], session_id)

    return imagenes

@app.post("/challenge", tags=["Challenges"])
def set_challenge( challenge: schemas.RegisterChallenge, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    challenge = challenge.__dict__
    challenge['tasks'] = [x.__dict__ for x in challenge['tasks']]

    resp = connection.set_challenge(db, challenge)
    username = access.decode_user(token)
    user = connection.get_user(db, username)
    if user.get("debug",False):
        auxiliar.debug_user("GET", "/image", challenge, resp, user['username'])

    return resp


@app.get("/promises/{session_id}", tags=["Visits"])
def get_promises_by_session( session_id: str, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    resp = connection.get_promises_images(db, session_id)
    username = access.decode_user(token)
    user = connection.get_user(db, username)
    if user.get("debug",False):
        auxiliar.debug_user("GET", "/image", {"session_id":session_id}, resp, user['username'])

    return resp


@app.get("/sync/{session_id}", tags=["Visits"])
def get_ids_in_server( session_id: str, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    respuestas = connection.get_images(db, session_id)

    imagenes = [x['resp_id'] for x in respuestas]

    username = access.decode_user(token)
    user = connection.get_user(db, username)
    if user.get("debug",False):
        auxiliar.debug_user("GET", "/image", {"session_id":session_id}, imagenes, user['username'])

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
    resp = connection.set_version(db,username,version)
    username_2 = access.decode_user(token)
    user = connection.get_user(db, username_2)
    if user.get("debug",False):
        auxiliar.debug_user("PUT", f"/version/{username}", {"username":username, "version":version}, resp, user['username'])

    return resp

@app.get("/deco")
def decode_token(token: str = Depends(oauth2_scheme)):
    return access.decode(token)

@app.post("/comment", tags=["Comments"])
def set_comment( store: schemas.RegisterComment, db: Session = Depends(get_db)):
    store = store.dict()
    resp = connection.set_comment(db, store)
    if "user_id" in store:
        username = store['user_id']
        user = connection.get_user(db, username)
    else:
        username = None
        user = None

    if not user or user.get("debug",False):
        auxiliar.debug_user("POST", "/comment", store, resp, username)

    return resp

@app.get("/configs", tags=["Users"])
def get_configs(db: Session = Depends(get_db)):
    return connection.get_configs(db)
