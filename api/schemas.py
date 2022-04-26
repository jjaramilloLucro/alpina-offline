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

class RespuestaBase(BaseModel):
    session_id: str
    uid: str
    document_id: str
    id_task: int
    lat: Optional[float]
    lon: Optional[float]
    store: Optional[str]
    imgs: List[str] = list()

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
    role: str
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

class CommentBase(BaseModel):
    session_id: str
    img_id: Optional[str]
    user_id: str
    comment: str
    event: str


######## Clases API (Input)
class RegisterAnswer(RespuestaBase):
    pass

class RegisterChallenge(DesafioBase):
    pass

class RegisterUser(UsuarioBase):
    pass

class RegisterStore(TiendasBase):
    pass

class RegisterComment(CommentBase):
    pass

######## Clases BD (Output)
class Answer(RespuestaBase):
    created_at: datetime.datetime

class Challenge(DesafioBase):
    expire: datetime.datetime

class User(UsuarioBase):
    version: Optional[str]
    isActive: bool

class Store(TiendasBase):
    pass

class Comment(CommentBase):
    created_at: datetime.datetime