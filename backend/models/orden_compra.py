from datetime import datetime
from pydantic import BaseModel


class ItemOrden(BaseModel):
    tipo_ticket: str
    cantidad: int
    precio_unitario: float


class OrdenCompra(BaseModel):
    usuario_id: str
    evento_id: str
    fecha_compra: datetime
    estado: str
    confirmado: bool
    items: list[ItemOrden]
    total: float