from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

######## Clases BASE
class ImagenBase(BaseModel):
    img: str
    identificado: List[str]

class RespuestaBase(BaseModel):
    session_id: str = Field(example="10fb6c43e04c45b987d4b07484864658")
    uid: str = Field(example="3133459997")
    document_id: str = Field(example="74")
    id_task: int = Field(Example=1)
    lat: Optional[float] = Field(example=6.2745088)
    lon: Optional[float] = Field(example=-75.5788499)
    store: Optional[str] = Field(example="9000813-28-DISTRITIENDAS BUENAVENTURA")
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
    store_key: str
    client_id: str
    user_id: str
    zone_id: str
    name: str
    city: str
    direction: str
    category: str
    tipology: str
    day_route: list
    add_exhibition: list
    channel: str
    subchannel: str
    chain_distributor: str
    leader: str
    group: str
    lat: float
    lon: float

class CommentBase(BaseModel):
    session_id: Optional[str]
    img_id: Optional[str]
    user_id: Optional[str]
    comment: str
    event: str


class GroupBase(BaseModel):
    name: str
    challenge: int = 1


class ProductMissingBase(BaseModel):
    class_name: str = Field(example="Bonyurt Zucaritas 170g")
    family: str = Field(example="BON YURT")
    category: str = Field(example="DERIVADOS LACTEOS")
    segment : str = Field(example="PLATAFORMA")
    territory: str = Field(example="DIVERSIÓN")
    sku: str = Field(example="8602")
    exist: bool = Field(example=True)
    class Config:
        fields = {
            'class_name': 'class'
        }


class MissingsBase(BaseModel):
    finish: bool = Field(example=True)
    sync: bool = Field(example=True)
    missings: List[ProductMissingBase]

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

class RegisterGroup(GroupBase):
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
    isActive: bool

class Comment(CommentBase):
    created_at: datetime.datetime

class Group(GroupBase):
    id: int

class Missings(MissingsBase):
    pass