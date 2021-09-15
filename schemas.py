from pydantic import BaseModel
from typing import Optional, List
import datetime

######## Clases BASE
class ImagenBase(BaseModel):
    img: str
    identificado: List[str]

class FotoBase(BaseModel):
    id: int
    imgs: List[dict] = list()
    resp: List[str] = list()

class RespuestaBase(BaseModel):
    uid: str
    document_id: str
    lat: float
    lon: float
    respuestas: List[FotoBase]

class TasksBase(BaseModel):
    title: str
    body: str
    ref_img: str
    id: int
    type: str
    required: bool
    options: List[str] = list()
    condicional: Optional[dict] = dict()

class DesafioBase(BaseModel):
    duracion:int
    name:str
    document_id: str
    tasks: List[TasksBase]

######## Clases API (Input)
class RegistroRespuesta(RespuestaBase):
    pass

class RegistroDesafio(DesafioBase):
    pass

######## Clases BD (Output)
class Respuesta(RespuestaBase):
    datetime: datetime.datetime

class Desafio(DesafioBase):
    expire: datetime.datetime
