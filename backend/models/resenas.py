from datetime import datetime
from pydantic import BaseModel


class Resena(BaseModel):
    usuario_id: str
    evento_id: str
    puntuacion: int
    comentario: str | None = None
    fecha_resena: datetime