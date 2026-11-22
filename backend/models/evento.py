from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Coordenadas(BaseModel):
    latitud: float
    longitud: float


class Recinto(BaseModel):
    nombre: str
    direccion: str
    ciudad: str
    capacidad: int = Field(gt=0)
    coordenadas: Coordenadas


class Ticket(BaseModel):
    tipo: str
    precio: float = Field(ge=0, allow_inf_nan=False)
    stock_inicial: int = Field(ge=0)
    stock_disponible: int = Field(ge=0)
    es_vip: bool

    @model_validator(mode="after")
    def validar_stock(self):
        if self.stock_disponible > self.stock_inicial:
            raise ValueError("El stock disponible no puede superar al stock inicial.")
        return self


class Evento(BaseModel):
    codigo_lugar: str
    nombre: str
    categoria: str
    descripcion: str
    fecha_evento: datetime
    estado: Literal["programado", "finalizado", "cancelado"]
    recinto: Recinto
    tickets_disponibles: list[Ticket] = Field(min_length=1)