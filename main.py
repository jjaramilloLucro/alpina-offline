from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import exc
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
        "name": "Upload - Users",
        "description": "Upload services for Alpunto service.",
    },
    {
        "name": "Upload - Stores",
        "description": "Upload services for Alpunto service.",
    }
]

version = "2.4.1"

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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print('*'*50)
    print("Body Validation Error:")
    print(exc)
    print('*'*50)
    print(request)
    print('*'*50)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

accepted_content_media = ['image/jpeg', 'image/png']

##### URLS
@app.post("/token", tags=["Users"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    ## Get OAuth service for token validation

    ### Args:
        username: User Identification logged for application.
        password: Password stored for the user.
        client_id: Client identification from endpoint.
        client_secret: Client secret from endpoint.

    ### Raises:
        HTTPException: 401. Unauthorized for wrong credentials.

    ### Returns:
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
        data={"user": cliente["uid"], "client_id": form_data.client_id}
    )
    resp = {"access_token": access_token, "token_type": "bearer"}
    if debug:
        entrada = {"username":form_data.username, "password": form_data.password}
        auxiliar.debug_user("POST", "/token", entrada, resp, username)
    return resp


@app.get("/ping", tags=["Test"])
def ping():
    """
    ## Health Check service for the endpoint.

    ### Returns:
        Boolean: True if service is working.
    """
    return True


@app.post("/image_test/image", tags=['Test'])
async def test_recognition_image(file: UploadFile = File(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme) ):
    """
    ## Generate visual test for Lucro Image Recognition Service for Alpina.

    ### Args:
        file: Image to Upload and test.

    ### Returns:
        file: Image with the bounding box for the image recognition for Alpina.
    """
    if file.content_type not in accepted_content_media:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Only accept {' or '.join(accepted_content_media)} Content-Type."
        )

    _, _, image, e = auxiliar.test_image_service(file, db, "prueba")
    if image:
        return FileResponse(image)
    else:
        return e

@app.post("/image_test/recognition", tags=['Test'])
async def test_recognition_plain(file: UploadFile = File(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme) ):
    """
    ## Generate plain test for Lucro Image Recognition Service for Alpina.

    ### Args:
        file: Image to Upload and test.

    ### Returns:
        list[Porducts]: Array for image recognition for Alpina.
    """
    if file.content_type not in accepted_content_media:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Only accept {' or '.join(accepted_content_media)} Content-Type."
        )

    _, trans, _, e = auxiliar.test_image_service(file, db, "prueba")
    return {"results": trans, "error": e}

@app.post("/answer", tags=["Visits"])
async def set_answer(answer: schemas.RegisterAnswer, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme) ):
    """
    ## Set the array of an answer to register in Alpunto.

    ### Args:
        session_id (str): Session_id to register in the visit.
        uid (str): Identification of the user which are realizing the visit.
        document_id (str): Identification of the group which the essentials portfolio will be evaluated.
                           For Example:
                           - "2" for essentials portfolio for "DISAY LTDA".
                           - "77" for essentials porfolio for "TIENDAS Y MARCAS MANIZALEZ".
                           - "485" for essentials portfolio for "ALPINA GALAPA".
        lat (float): Latitude of the response.
        lon (float): Longitude of the response.
        store (str): Store key which was visited. Composed of {client_id}-{zone_id}-{distributor_id}
                     For example:
                     - "8000012013-176SE-482" for "OXXO ESTRELLA NORTE".
        imgs (List[str]): List of name of images to send to server.
                          For example:
                          - ["34", "56", "78"] if the client is going to send the images "34.jpg", "56.jpg" and "78.jpg" 

    ### Raises:
        HTTPException: 404. When an User, Store or Client is not found.
                          
    ### Returns:
        Response: A JSON with the response saved in the Alpunto DB.
    """
    answer = answer.dict()
    respuestas = connection.get_respuestas(db, answer['session_id'])
    existe = [x.split('-')[-1] for resp in respuestas for x in resp['imgs']]
    answer['imgs'] = list(set(answer['imgs']) - set(existe))
    answer['imgs'] = [answer['session_id'] + '-' + x for x in answer['imgs']]
    answer["created_at"]= auxiliar.time_now()
    decode = access.decode(token)[0]
    username = access.decode_user(token)
    user = connection.get_user(db, username)
    try:
        resp = connection.guardar_resultados(db, answer, decode['client_id'])
        if user.get("debug",False):
            auxiliar.debug_user("POST", "/answer", answer, resp, user['uid'], answer['session_id'])
        return resp
    except exc.IntegrityError as e:
        error = str(e.orig).split("\n")
        error = error[-2]
        print(error)
        if user.get("debug",False):
            auxiliar.debug_user("POST", "/answer", answer, error, user['uid'], answer['session_id'])
        db.rollback()
        raise HTTPException(status_code=404, detail=error)
    

@app.post("/answer/{session_id}", tags=["Visits"])
async def send_image(session_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme), 
    imgs: Optional[List[UploadFile]] = File(None)
):
    """
    ## Send Images to register a Visit.

    ### Args:
        session_id (str): Session_id for the visit to register.
        imgs (List[UploadFile]): List of Images send via multipart to register to the session_id.

    ### Returns:
        List[str]: List of images received in server.
    """
    for img in imgs:
        if img.content_type not in accepted_content_media:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Only accept {' or '.join(accepted_content_media)} Content-Type."
            )

    username = access.decode_user(token)
    user = connection.get_user(db, username)
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
        imagenes = auxiliar.save_answer(db, body, user.get("username"))
        background_tasks.add_task(auxiliar.actualizar_imagenes, db=db, username=username, imagenes = imagenes, session_id=session_id)
    
    del body['imagenes']
    resp = falt

    if user.get("debug",False):
        auxiliar.debug_user("POST", f"/answer/{session_id}", body, resp, user['uid'], session_id)
    return resp

@app.get("/", tags=["Users"])
async def get_session_id( token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    ## Gets session_id to register a visit.

    ### Returns:
        session_id: Id of session to register.
    """
    resp = auxiliar.session_id(db)
    username = access.decode_user(token)
    user = connection.get_user(db, username)
    if user.get("debug",False):
        auxiliar.debug_user("GET", "/", "", resp, user['uid'])
    return resp

@app.get("/missings", tags=["Essentials"], response_model=schemas.Missings)
def get_missings(session_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    ## Get the missings from the portfolio.

    ### Args:
        session_id (str): Session_id to get the missings portfolio.

    ### Returns:
        List[Products]: List of products of portfolio with the exist flag. 
    """
    username = access.decode_user(token)
    user = connection.get_user(db, username)
    faltantes = connection.get_faltantes(db, session_id)
    if faltantes:
        resp =  {"finish":True, "sync":True, "missings":faltantes}
    else:
        promises = connection.get_promises_images(db, session_id)
        serv = connection.get_images(db, session_id)
        serv = [x['resp_id'] for x in serv]
        if not set(promises) == set(serv):
            resp = {"finish":False, "sync":False, "missings":list()}

        else:
            final, faltantes = connection.calculate_faltantes(db, session_id, username)
            if final:
                connection.set_faltantes(db, session_id, faltantes)
            resp = {"finish":final, "sync":True, "missings":faltantes}

    if user.get("debug",False):
        auxiliar.debug_user("GET", "/missings", {"session_id": session_id}, resp, user['uid'], session_id)

    return resp


@app.get("/image", tags=["Essentials"])
async def get_image(session_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    respuestas = connection.get_respuestas(db, session_id)
    imgs = connection.get_images(db, session_id)
    imgs = {x['resp_id']:auxiliar.get_raw_recognitions(db, x['data']) for x in imgs}

    imagenes = [{"imgs":x, "data":imgs[x]} for resp in respuestas for x in resp['imgs']]

    username = access.decode_user(token)
    user = connection.get_user(db, username)
    if user.get("debug",False):
        auxiliar.debug_user("GET", "/image", {"session_id": session_id}, imagenes, user['uid'], session_id)

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



@app.get("/users", tags=["Upload - Users"], response_model=List[schemas.User])
def get_all_users(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)):
    """
    ## Get an User for Alpunto Application.

    ### Response:
        List[User]: A list of registered user in the Alpunto app.
    """
    return connection.get_all_user(db)


@app.get("/user/{uid}", tags=["Upload - Users"], response_model=schemas.User)
def get_user_by_uid(uid: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)):
    """
    ## Get an User for Alpunto Application.

    ### Args:
        uid: Identification of the user in the application.

    ### Raise:
        HTTPException: 404. If the user does not exist.

    ### Response:
        User: A registered user in the Alpunto app.
    """
    user = connection.get_user(db, uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The user with uid {uid} does not exist."
        )
    return user


@app.post("/user", tags=["Upload - Users"], response_model=schemas.User)
def create_or_update_user(resp: schemas.RegisterUser,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)):
    """
    ## Create an User for Alpunto Application. If uid exist, then it replace its information.

    ### Args:
        uid: Identification of the user in the application.
        password: Password to validate on requests.
        name: User complete name.
        telephone: Optional. Telephone of the user.

    ### Response:
        User: A registered user in the Alpunto app.
    """
    user = resp.__dict__
    if user['uid'] == user['password']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password can't be same as username"
        )
    user['password'] = access.get_password_hash(user['password'])
    user['register_at'] = auxiliar.time_now()
    user['register_by'] = access.decode_user(token)
    if connection.get_user(db, user['uid']):
        user = connection.update_user(db, user)
    else:
        user = connection.set_user(db, user)
    return user


@app.put("/user/{uid}", tags=["Upload - Users"], response_model=schemas.User)
def activate_user_by_uid(uid: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)):
    """
    ## Activate an User for Alpunto Application.

    ### Args:
        uid: Identification of the user in the application.

    ### Raise:
        HTTPException: 404. If the user does not exist.

    ### Response:
        User: A registered user in the Alpunto app.
    """
    user = connection.get_user(db, uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The user with uid {uid} does not exist."
        )
    user['deleted_at'] = None
    user['deleted_by'] = None
    user['isActive'] = True
    user['register_at'] = auxiliar.time_now()
    user['register_by'] = access.decode_user(token)
    user = connection.update_user(db, user)
    return user

@app.delete("/user/{uid}", tags=["Upload - Users"], response_model=schemas.User)
def delete_user_by_uid(uid: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)):
    """
    ## Delete an User for Alpunto Application.

    ### Args:
        uid: Identification of the user in the application.

    ### Raise:
        HTTPException: 404. If the user does not exist.

    ### Response:
        User: A registered user in the Alpunto app.
    """
    user = connection.get_user(db, uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The user with uid {uid} does not exist."
        )
    user['deleted_at'] = auxiliar.time_now()
    user['deleted_by'] = access.decode_user(token)
    user['isActive'] = False
    user = connection.update_user(db, user)
    return user


@app.get("/stores", tags=["Upload - Stores"], response_model=List[schemas.Store])
def get_all_stores(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)):
    """
    ## Get an Store for Alpunto Application.

    ### Response:
        List[Store]: A list of registered stores in the Alpunto app.
    """
    return connection.get_all_stores(db)



@app.get("/store/{store_key}", tags=["Upload - Stores"], response_model=schemas.Store)
def get_store_by_store_key(store_key: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)):
    """
    ## Get an Store for Alpunto Application.

    ### Args:
        store_key: Identification of the store in the application.

    ### Raise:
        HTTPException: 404. If the store does not exist.

    ### Response:
        Store: A registered store in the Alpunto app.
    """
    store = connection.get_tienda_sql(db, store_key)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The store with store_key {store_key} does not exist."
        )
    return store

@app.post("/store", tags=["Upload - Stores"], response_model=schemas.Store)
def create_or_update_store(resp: schemas.RegisterStore,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)):
    """
    ## Create an Store for Alpunto Application. If store_key exist, then it replace its information.

    ### Args:
        store_key: Identification of the store in the application. Composed of {client_id}-{zone_id}-{distributor_id}
                     For example:
                     - "8000012013-176SE-482" for "OXXO ESTRELLA NORTE"
        client_id: Id of the store.
        zone_id: Id for the zone.
        distributor_id: Id for the Distributor.
        uid: Identification of the User who visit the Store.
        name: Name of the Store.
        city: City or region of the Store.
        address: Address of the Store.
        category: Category of the Store.
        tipology: Tipology of the Store.
        channel: Channel of the Store.
        subchannel: Subchannel of the Store.
        leader: Leader of the Store.
        lat: Optional. Latitude of the Store.
        lon: Optional. Longitude of the Store.

    ### Raise:
        HTTPException: 404. If the User or Client does not exist.

    ### Response:
        Store: A registered Store in the Alpunto app.
    """
    store = resp.__dict__
    store['created_at'] = auxiliar.time_now()
    store['created_by'] = access.decode_user(token)

    try:
        if connection.get_tienda_sql(db, store['store_key']):
            store = connection.update_tienda(db, store)
        else:
            store = connection.set_tienda(db, store)
        return store
    except exc.IntegrityError as e:
        error = str(e.orig).split("\n")
        error = error[-2]
        print(error)
        db.rollback()
        raise HTTPException(status_code=404, detail=error)


@app.put("/store/{store_key}", tags=["Upload - Stores"], response_model=schemas.Store)
def activate_store_by_store_key(store_key: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)):
    """
    ## Activate an Store for Alpunto Application.

    ### Args:
        store_key: Identification of the Store in the application.

    ### Raise:
        HTTPException: 404. If the Store does not exist.

    ### Response:
        Store: A registered store in the Alpunto app.
    """
    store = connection.get_tienda_sql(db, store_key)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The store with store_key {store_key} does not exist."
        )
    store['deleted_at'] = None
    store['deleted_by'] = None
    store['isActive'] = True
    store['created_at'] = auxiliar.time_now()
    store['created_by'] = access.decode_user(token)
    store = connection.update_tienda(db, store)
    return store

@app.delete("/store/{store_key}", tags=["Upload - Stores"], response_model=schemas.Store)
def delete_store_by_store_key(store_key: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)):
    """
    ## Delete an User for Alpunto Application.

    ### Args:
        store_key: Identification of the Store in the application.

    ### Raise:
        HTTPException: 404. If the Store does not exist.

    ### Response:
        Store: A registered store in the Alpunto app.
    """
    store = connection.get_tienda_sql(db, store_key)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The store with store_key {store_key} does not exist."
        )
    store['deleted_at'] = auxiliar.time_now()
    store['deleted_by'] = access.decode_user(token)
    store['isActive'] = False
    store = connection.update_tienda(db, store)
    return store
