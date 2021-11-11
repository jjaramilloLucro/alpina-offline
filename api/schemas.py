from pydantic import BaseModel
from typing import Optional, List
import datetime

######## Clases BASE
class ImagenBase(BaseModel):
    img: str
    identificado: List[str]

class Prueba(BaseModel):
    img: str
    id: str
    session_id: str

class FotoBase(BaseModel):
    id: int
    imgs: List[dict] = list()
    resp: List[str] = list()

class RespuestaBase(BaseModel):
    uid: str
    document_id: str
    respuestas: List[FotoBase]

class TasksBase(BaseModel):
    title: str
    body: str
    ref_img: str
    id: int
    type: str
    required: bool
    store: bool = False
    options: List[str] = list()
    condition: Optional[dict] = dict()

class DesafioBase(BaseModel):
    duration:int
    name:str
    tasks: List[TasksBase]

class UsuarioBase(BaseModel):
    username: str
    password: str
    name: str
    group: List[int]

class TiendasBase(BaseModel):
    client_id: str
    user_id: str
    zone_id: str
    name: str
    direction: str
    category: str
    tipology: str
    route: str
    add_exhibition: List[dict]

######## Clases API (Input)
class RegisterAnswer(RespuestaBase):
    pass

class RegisterChallenge(DesafioBase):
    pass

class RegisterUser(UsuarioBase):
    pass

class RegisterStore(TiendasBase):
    pass

######## Clases BD (Output)
class Answer(RespuestaBase):
    datetime: datetime.datetime

class Challenge(DesafioBase):
    expire: datetime.datetime

class User(UsuarioBase):
    pass

class Store(TiendasBase):
    pass