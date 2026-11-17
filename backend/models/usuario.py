from datetime import datetime
from pydantic import BaseModel


class Usuario(BaseModel):
    rut: str
    nombre: str
    email: str
    telefono: str
    rol: str
    fecha_nacimiento: datetime
    activo: bool