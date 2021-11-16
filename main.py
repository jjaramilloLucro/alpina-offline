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
        "name": "CSV Files",
        "description": "Upload data from CSV files.",
    },
]

version = "3.1.7"

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

@app.post("/user", tags=["Users"], response_model=schemas.User)
def create_user(resp: schemas.RegisterUser, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = resp.__dict__
    user['password'] = access.get_password_hash(user['password'])
    connection.set_user(db, user)
    return user

@app.get("/challenges", tags=["Challenges"])
def get_challenges(username:str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = connection.get_user(db, username)
    tiendas = connection.get_tienda_user(db, user['username'])
    dia = auxiliar.time_now().weekday()
    puntos = [x['name'] for x in tiendas if dia in x['day_route']]
    grupo = connection.get_grupo(db, user['group'])
    challenges = [{"group_id":g.id,'challenge':connection.get_challenge(db, x)} for g in grupo for x in g.challenges]
    id_tienda = 0
    for i in range(len(challenges)):
        challenges[i]['challenge']['document_id'] = str(challenges[i]['group_id']) + '__' + str(challenges[i]['challenge']['challenge_id'])
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
async def set_answer(background_tasks: BackgroundTasks, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme),
    session_id: str = Form(...), resp: Optional[List[str]] = Form(None), imgs: Optional[List[UploadFile]] = File(None), document_id: str = Form(...), 
    uid: str = Form(...), id_preg: int = Form(...), lat: Optional[str] = Form(None), lon: Optional[str] = Form(None), store: Optional[bool] =  Form(False)
):
    start_time = time.time()
    imgs = imgs if imgs else list()
    resp = resp[0] if resp else ""

    ids = [file.filename.split(".")[0] for file in imgs]
    respuestas = connection.get_respuestas(db, session_id)
    existe = [x.split('-')[1] for resp in respuestas for x in resp['imgs']]
    falt = list(set(ids)-set(existe))
    if not falt and resp == '':
        body =  {
            "uid": uid,
            "document_id": document_id,
            "session_id": session_id,
            "created_at": auxiliar.time_now(),
            "imgs": ids
        }
    else:
        imgs = [file for file in imgs if file.filename.split(".")[0] in falt]
        body =  {
            "uid": uid,
            "document_id": document_id,
            "session_id": session_id,
            'id_task':id_preg, 
            'img_ids': [file.filename.split(".")[0] for file in imgs],
            'imgs': [file.file.read() for file in imgs], 
            "lat": lat,
            "lon": lon,
            "store": store,
            "resp": resp,
            "created_at": auxiliar.time_now()
        }
        
        imagenes = auxiliar.save_answer(db, body)
        background_tasks.add_task(auxiliar.actualizar_imagenes, db=db, imagenes = imagenes, session_id=session_id)
    print("Total time:")
    print("--- %s seconds ---" % (time.time() - start_time))
    return body

@app.get("/", tags=["Users"])
async def get_session_id( token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return auxiliar.session_id(db)

@app.get("/missings", tags=["Essentials"])
def get_missings(session_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    faltantes = connection.get_faltantes(db, session_id)
    if faltantes:
        return {"finish":True, "missings":faltantes['products']}
    else:
        final, faltantes = connection.calculate_faltantes(db, session_id)
        if final:
            connection.set_faltantes(db, session_id, faltantes)
        return {"finish":final, "missings":faltantes}

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

@app.get("/sync/{session_id}/{id_task}", tags=["Visits"])
def get_ids_by_session_and_task( session_id: str, id_task:int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    respuestas = connection.get_respuestas(db, session_id)

    imagenes = [x for resp in respuestas if resp['id_task']==id_task for x in resp['imgs']]

    return imagenes

@app.get("/sync/{session_id}", tags=["Visits"])
def get_ids_by_session( session_id: str, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    respuestas = connection.get_respuestas(db, session_id)

    imagenes = [x for resp in respuestas for x in resp['imgs']]

    return imagenes

@app.post("/files/stores", tags=["CSV Files"])
def upload_stores( file: UploadFile = File(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    return connection.upload_stores(db, file.file)