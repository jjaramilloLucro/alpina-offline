from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks, File, UploadFile, Path, Query

from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from sqlalchemy.orm import Session

from api import connection, access, schemas, auxiliar
import models, time
from database import SessionLocal, engine

DOCS_TITLE = "Admin API AlPunto"
DOCS_VERSION = "4.5.2 - Admin"

######## Configuración de la app
app = FastAPI(title=DOCS_TITLE,
    description="Administrador de funciones y API para la app de AlPunto.",
    version=DOCS_VERSION,
    )

def my_schema():
   
   openapi_schema = get_openapi(
       title=DOCS_TITLE,
       version=DOCS_VERSION,
       routes=app.routes,
   )
   openapi_schema["info"] = {
       "title" : DOCS_TITLE,
       "version" : DOCS_VERSION,
       "description" : "Administrador de funciones y API para la app de AlPunto.",
       "termsOfService": "",
       "contact": {
           "name": "Carlos Hernandez",
           "email": "c.hernandez@lucro-app.com"
       },
   }

   openapi_schema["tags"] = [
    {
        "name": "Servicios de Administrador",
        "description": "Servicios para la creación y modificación de grupos, infaltables, usuarios y rutero.",
    },
    {
        "name": "Endpoints",
        "description": "Servicios utilizados por la aplicación para el manejo y guardado de datos.",
    },
    {
        "name": "Otros",
        "description": "",
    },
]
   app.openapi_schema = openapi_schema
   return app.openapi_schema

app.openapi = my_schema

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
@app.post("/token", tags=["Endpoints"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    username = form_data.username
    username = username.replace(" ","")
    if username == form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password can't be same as username",
            headers={"WWW-Authenticate": "Bearer"},
        )
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


@app.get("/challenges", tags=["Endpoints"])
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


@app.get("/stores", tags=["Endpoints"])
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


@app.get("/challenges/{id}", tags=["Endpoints"])
def get_challenges(id:str, token: str = Depends(oauth2_scheme),  db: Session = Depends(get_db)):
    return connection.get_challenge(db, id)


@app.post("/prueba", tags=['Otros'])
async def prueba_maquina(resp: schemas.Prueba, db: Session = Depends(get_db) ):
    resp = resp.__dict__
    return auxiliar.identificar_producto(db, resp['img'], resp['id'], resp['session_id'])


@app.get("/decode", tags=['Otros'])
async def decode_imagen(url: str ):
    return auxiliar.decode(url)


@app.get("/code", tags = ['Otros'])
async def code(cod:str):
    return access.get_password_hash(cod)


@app.post("/answer", tags=["Endpoints"])
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


@app.post("/answer/{session_id}", tags=["Endpoints"])
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


@app.get("/", tags=["Endpoints"])
async def get_session_id( token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return auxiliar.session_id(db)


@app.get("/missings", tags=["Endpoints"])
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

@app.get("/image", tags=["Endpoints"])
async def get_image(session_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    respuestas = connection.get_respuestas(db, session_id)
    imgs = connection.get_images(db, session_id)
    imgs = {x['resp_id']:x['data'] for x in imgs}

    imagenes = [{"id_preg":resp['id_task'],"imgs":x, "data":imgs[x]} for resp in respuestas for x in resp['imgs']]
    return imagenes

@app.post("/challenge", tags=["Endpoints"])
def set_challenge( challenge: schemas.RegisterChallenge, db: Session = Depends(get_db),token: str = Depends(oauth2_scheme)):
    challenge = challenge.__dict__
    challenge['tasks'] = [x.__dict__ for x in challenge['tasks']]
    return connection.set_challenge(db, challenge)


@app.get("/promises/{session_id}", tags=["Endpoints"])
def get_promises_by_session( session_id: str, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    return connection.get_promises_images(db, session_id)


@app.get("/sync/{session_id}", tags=["Endpoints"])
def get_ids_in_server( session_id: str, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    respuestas = connection.get_images(db, session_id)

    imagenes = [x['resp_id'] for x in respuestas]

    return imagenes


@app.get("/ping", tags=["Endpoints"])
def ping():
    return True


@app.get("/sync", tags=["Endpoints"])
def sync_day_route():
    return auxiliar.time_now().weekday()


@app.put("/version/{username}", tags=["Endpoints"])
def user_version(username: str, version: str,db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    return connection.set_version(db,username,version)


@app.get("/deco", tags=['Otros'])
def decode_token(token: str = Depends(oauth2_scheme)):
    return access.decode(token)


@app.post("/comment", tags=["Endpoints"])
def set_comment( store: schemas.RegisterComment, db: Session = Depends(get_db)):
    return connection.set_comment(db, store.dict())


@app.get("/configs", tags=["Endpoints"])
def get_configs(db: Session = Depends(get_db)):
    return connection.get_configs(db)


@app.get("/group", tags=["Servicios de Administrador"])
def get_groups(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    ## Devuelve todos los grupos habilitados en la aplicación.

    ### Resultado:
        Grupos: Lista de Grupos Disponibles.
    """
    return connection.get_grupos(db)


@app.get("/group/{id}", tags=["Servicios de Administrador"])
def get_group(id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    ## Devuelve el grupo solicitado.

    ### Parámetros:
        id: Id del grupo a consultar.

    ### Resultado:
        Grupo: Grupo con el id solicitado.
    """
    return connection.get_grupo(db,[id])

@app.post("/group", tags=["Servicios de Administrador"], response_model=schemas.Group)
def set_group(
    resp: schemas.RegisterGroup,
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
    ):
    """
    ## Crea un Grupo para la Aplicación

    ### Parámetros:
        name: Nombre del Grupo a crear.
        challenge: Seleccione uno de los siguientes casos:
            - 1: Para Canal Moderno (Categoria).
            - 2: Para Canal Moderno (Bloque de Marca).
            - 3: Para Minimercado/SE.
            - 4: Para Tiendas.

    ### Resultado:
        Grupo: Grupo Creado
    """
    grupo = resp.__dict__
    return connection.set_grupo(db,grupo)


@app.post("/essentials", tags=["Servicios de Administrador"] )
def set_essentials(group_id: str, productos: List[dict], token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    ## Crea el pórtafolio de Infaltables para el grupo específico.

    ### Parámetros:
        id: Id del grupo a establecer los Infaltables.
        products: Lista de productos a ingresar como portafolio de infaltables.

    ### Resultado:
        Infatables: Lista de Productos junto al id del grupo asociado.
    """
    faltantes = {"group_id":group_id,"prods":productos}
    return connection.set_infaltables(db, faltantes)


@app.post("/user", tags=["Servicios de Administrador"], response_model=schemas.User)
def create_user(resp: schemas.RegisterUser, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    ## Crea un usuario dentro de la aplicación.

    ### Parámetros:
        username: Telefono del usuario a registrar.
        password: Clave a utilizar en la aplicación.
        name: Nombre del usuario.
        role: Rol al que pertenece el usuario.
        group: id de los grupos al que eprtenece el usaurio.

    ### Resultado:
        Usuario: Usuario registrado en la aplicación.
    """
    user = resp.__dict__
    if user['username'] == user['password']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password can't be same as username"
        )
    user['password'] = access.get_password_hash(user['password'])
    user = connection.set_user(db, user)
    return user


@app.post("/files/users", tags=["Servicios de Administrador"])
def upload_users( file: UploadFile = File(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    ## Realiza una carga masiva de Usuarios.

    ### Parámetros:
        file: archivo csv con los campos solicitados.

    ### Resultado:
        Mensaje: Mensaje de éxito con la cantidad de usuarios creados.
    """
    return connection.upload_users(db, file.file)


@app.post("/files/stores", tags=["Servicios de Administrador"])
def upload_stores( file: UploadFile = File(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    ## Realiza una carga masiva de Tiendas.

    ### Parámetros:
        file: archivo csv con los campos solicitados.

    ### Resultado:
        Mensaje: Mensaje de éxito con la cantidad de tiendas creadas.
    """
    return connection.upload_stores(db, file.file)