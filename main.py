from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI, HTTPException, status, BackgroundTasks, File, UploadFile

import connection, access, schemas
import datetime

tags_metadata = [
    {
        "name": "Modulo API",
        "description": "Servicios de API.",
    },
]

version = "1.0.1"

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
async def get_desafios(token: str = Depends(oauth2_scheme)):
    return connection.getAllChallenges()

@app.get("/prueba")
async def prueba(cod:str):
    return access.get_password_hash(cod)

@app.get("/infaltables", tags=["Modulo API"])
async def get_infaltables(token: str = Depends(oauth2_scheme)):
    return connection.getAllInfaltables()

@app.post("/registrar", response_model=schemas.Respuesta, tags=["Modulo API"])
async def root(resp: schemas.RegistroRespuesta , token: str = Depends(oauth2_scheme)):
    
    return {**resp.__dict__, "datetime": datetime.datetime.now()}