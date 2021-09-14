from pydantic import BaseModel
from typing import Optional, List
import datetime

######## Clases BASE
class Fotobase(BaseModel):
    img: List[str]
    identificado: List[str]

class RespuestaBase(BaseModel):
    uid: str
    document_id: str
    lat: float
    lon: float
    respuestas: List[Fotobase]


######## Clases API (Input)
class RegistroRespuesta(RespuestaBase):
    pass


######## Clases BD (Output)
class Respuesta(RespuestaBase):
    datetime: datetime.datetime
