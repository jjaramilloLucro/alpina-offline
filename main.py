from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from api import connection, access, schemas, auxiliar
import models
from database import SessionLocal, engine

tags_metadata = [
    {
        "name": "Test",
        "description": "Test Services.",
    },
    {
        "name": "Users",
        "description": "User services."
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
        "name": "Upload",
        "description": "Upload services for Alpunto service.",
    },
]

version = "1.1.0"

######## Configuración de la app
app = FastAPI(title="API Alpina Alpunto",
    description="API for Alpina Alpunto app.",
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
    """Get OAuth service for token validation

    Args:
        username: User Identification logged for application.
        password: Password stored for the user.
        client_id: Client identification from endpoint.
        client_secret: Client secret from endpoint.

    Raises:
        HTTPException: 401. Unauthorized for wrong credentials.

    Returns:
        Headers: Access token for client requests.
    """
    if not(form_data.client_id and form_data.client_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please priovide the client credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
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
            entrada = {
                "username":form_data.username,
                "password": form_data.password,
                "client_nid":form_data.client_id,
                "client_secret":form_data.client_secret}
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


@app.get("/ping", tags=["Test"])
def ping():
    """Health Check service for the endpoint.

    Returns:
        Boolean: True if service is working.
    """
    return True


@app.post("/image_test/image", tags=['Test'])
async def test_recognition_image(file: UploadFile = File(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme) ):
    """Generate visual test for Lucro Image Recognition Service for Alpina.

    Args:
        file: Image to Upload and test.

    Returns:
        file: Image with the bounding box for the image recognition for Alpina.
    """
    _, image = auxiliar.test_image_service(file)
    if image:
        return FileResponse(image)
    else:
        return None

@app.post("/image_test/recognition", tags=['Test'])
async def test_recognition_plain(file: UploadFile = File(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme) ):
    """Generate plainn test for Lucro Image Recognition Service for Alpina.

    Args:
        file: Image to Upload and test.

    Returns:
        list[Porducts]: Array for image recognition for Alpina.
    """
    a, _ = auxiliar.test_image_service(file)
    return a

@app.post("/answer", tags=["Visits"])
async def set_answer(answer: schemas.RegisterAnswer, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme) ):
    answer = answer.dict()
    respuestas = connection.get_respuestas(db, answer['session_id'])
    existe = [x.split('-')[-1] for resp in respuestas for x in resp['imgs']]
    answer['imgs'] = list(set(answer['imgs'])-set(existe))
    answer['imgs'] = [answer['session_id']+'-'+x for x in answer['imgs']]
    #answer['resp'] = answer['resp'][0] if answer['resp'] else ""
    #answer['store'] = answer['resp'] != ""
    answer["created_at"]= auxiliar.time_now()
    resp = connection.guardar_resultados(db, answer)
    username = access.decode_user(token)
    user = connection.get_user(db, username)
    if user.get("debug",False):
        auxiliar.debug_user("POST", "/answer", answer, resp, user['username'], answer['session_id'])
    return resp

@app.post("/answer/{session_id}", tags=["Visits"])
async def send_image(session_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme), 
    imgs: Optional[List[UploadFile]] = File(None)
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

@app.get("/missings", tags=["Essentials"], response_model=schemas.Missings)
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
            resp = {"finish":final, "sync":True, "missings":faltantes}

    username = access.decode_user(token)
    user = connection.get_user(db, username)
    if user.get("debug",False):
        auxiliar.debug_user("GET", "/missings", {"session_id": session_id}, resp, user['username'], session_id)

    return resp


@app.get("/image", tags=["Essentials"])
async def get_image(session_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    respuestas = connection.get_respuestas(db, session_id)
    imgs = connection.get_images(db, session_id)
    imgs = {x['resp_id']:x['data'] for x in imgs}

    imagenes = [{"id_preg":resp['id_task'],"imgs":x, "data":imgs[x]} for resp in respuestas for x in resp['imgs']]

    username = access.decode_user(token)
    user = connection.get_user(db, username)
    if user.get("debug",False):
        auxiliar.debug_user("GET", "/image", {"session_id": session_id}, imagenes, user['username'], session_id)

    return imagenes


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



@app.post("/user", tags=["Upload"], response_model=schemas.User)
def create_user(resp: schemas.RegisterUser, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    ## Create an User for Alpunto Application.

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

@app.post("/token", tags=["Upload"], response_model=schemas.Store)
def upload_store(store: schemas.RegisterStore, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    
    return True

@app.get("/groups", tags=["Upload"], response_model=schemas.Group)
async def get_groups( token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get all gruops in Alpunto Application.

    Returns:
        List[Group]: List of groups.
    """
    username = access.decode_user(token)
    user = connection.get_user(db, username)
    resp = connection.get_grupos(db)
    if user.get("debug",False):
        auxiliar.debug_user("GET", "/", "", resp, user['username'])
    return resp


@app.post("/group", tags=["Upload"], response_model=schemas.Group)
def set_group(
    resp: schemas.RegisterGroup,
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
    ):
    """
    ## Set a Focus Group for Alpunto Essentials target.

    ### Args:
        name: Group Name to create.
        challenge: Select one of these:
            - 1: Canal Moderno (Categoria).
            - 2: Canal Moderno (Bloque de Marca).
            - 3: Minimercado/SE.
            - 4: Tiendas.

    ### Returns:
        group: Group succesfully created.
    """
    grupo = resp.__dict__
    return connection.set_grupo(db,grupo)


@app.post("/essentials", tags=["Upload"], response_model=schemas.Essentials )
def set_essentials(group_id: str, products: List[dict], token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    ## Create or Update the Essentials portfolio for a specific group (previously created).

    ### Args:
        group_id: Group Identification to set.
        products: Products portfolio to set.

    ### Returns:
        Essentials: List of Products with the associated id.
    """
    faltantes = {"group_id":group_id,"prods":products}
    return connection.set_infaltables(db, faltantes)

