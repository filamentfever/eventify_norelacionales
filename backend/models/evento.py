from datetime import datetime
from pydantic import BaseModel


class Coordenadas(BaseModel):
    latitud: float
    longitud: float


class Recinto(BaseModel):
    nombre: str
    direccion: str
    ciudad: str
    capacidad: int
    coordenadas: Coordenadas


class Ticket(BaseModel):
    tipo: str
    precio: float
    stock_inicial: int
    stock_disponible: int
    es_vip: bool


class Evento(BaseModel):
    codigo_lugar: str
    nombre: str
    categoria: str
    descripcion: str
    fecha_evento: datetime
    estado: str
    recinto: Recinto
    tickets_disponibles: list[Ticket]