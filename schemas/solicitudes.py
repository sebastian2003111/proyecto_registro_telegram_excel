from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

class Solicitud(BaseModel):
    estudiante: str = Field(min_length=2, max_length=100)
    tipo: str = Field(min_length=3, max_length=100)
    descripcion: str = Field(min_length=5, max_length=1000)
    estado: Literal[
        "PENDIENTE",
        "EN_PROCESO",
        "ATENDIDA",
        "CANCELADA",
        "RESUELTA"
    ] = "PENDIENTE"

class SolicitudRespuesta(Solicitud):
    id: int
    fecha: str

class EstadoActualizacion(BaseModel):
    estado: Literal[
        "PENDIENTE",
        "EN_PROCESO",
        "ATENDIDA",
        "CANCELADA",
        "RESUELTA"
    ]