from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
import datetime
######## Clases BASE
class ImagenBase(BaseModel):
    img: str
    identificado: List[str]

class RespuestaBase(BaseModel):
    session_id: str = Field(example="10fb6c43e04c45b987d4b07484864658")
    uid: str = Field(example="1030234879")
    document_id: str = Field(example="77")
    lat: Optional[float] = Field(example=6.2745088)
    lon: Optional[float] = Field(example=-75.5788499)
    store: Optional[str] = Field(example="9000813-28-77")
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
    uid: str = Field(example="1114815094")
    password: str = Field(example="1234")
    name: str = Field(example="CRISTIAN ALEJANDRO GUTIERREZ SAAVEDRA")
    telephone: Optional[str] = Field(example="3228469791")
    

class TiendasBase(BaseModel):
    store_key: str = Field(example="8000012013-176SE-482")
    client_id: str = Field(example="8000012013")
    zone_id: str = Field(example="176SE")
    distributor_id: str = Field(example="482")
    uid: str = Field(example="1030234879")
    name: str = Field(example="OXXO ESTRELLA NORTE")
    city: str = Field(example="Bogota")
    address: str = Field(example="CL 161 21 09")
    category: str = Field(example="Bronce")
    tipology: str = Field(example="SUPERMERCADOS INDEPENDIENTES")
    channel: str = Field(example="SE")
    subchannel: str = Field(example="SUP Supermdo Indepen")
    leader: str = Field(example="Carlos Luna")
    lat: Optional[float] = Field(example=6.2745088)
    lon: Optional[float] = Field(example=-75.5788499)

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
    sync: bool = Field(example=True)
    finish: bool = Field(example=True)
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
    register_at: datetime.datetime = Field(example=datetime.datetime.now())
    register_by: str = Field(example="Alpunto")
    isActive: Optional[bool] = Field(example=True)
    deleted_at: Optional[datetime.datetime] = Field(example=None)
    deleted_by: Optional[str] = Field(example=None)

    model_config = ConfigDict(from_attributes=True)

class Store(TiendasBase):
    created_at: datetime.datetime = Field(example=datetime.datetime.now())
    created_by: str = Field(example="Alpunto")
    isActive: Optional[bool] = Field(example=True)
    deleted_at: Optional[datetime.datetime] = Field(example=None)
    deleted_by: Optional[str] = Field(example=None)

    model_config = ConfigDict(from_attributes=True)

class Comment(CommentBase):
    created_at: datetime.datetime

class Group(GroupBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class Missings(MissingsBase):
    pass

class Essentials(BaseModel):
    group_id: int = Field(example=74)
    prods: List[ProductMissingBase]

class ReportModel(BaseModel):
    created_at: datetime.datetime = Field(example=datetime.datetime.now())
    store_key: str = Field(example="8000012013-176SE-482")
    uid: str = Field(example = "1030234879")
    session_id: str = Field(example = "10fb6c43e04c45b987d4b07484864658")
    missings: List[ProductMissingBase]

    model_config = ConfigDict(from_attributes=True)
    