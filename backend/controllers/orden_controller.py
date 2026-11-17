from fastapi import APIRouter, HTTPException

from backend.services.orden_service import listar_ordenes, obtener_orden

router = APIRouter(
    prefix="/api/v1/ordenes",
    tags=["Órdenes de compra"]
)


@router.get("/")
def obtener_ordenes():
    return listar_ordenes()


@router.get("/{orden_id}")
def filtro_por_id(orden_id: str):
    resultado = obtener_orden(orden_id)
    if not resultado:
        raise HTTPException(
            status_code=404,
            detail="Orden no encontrada"
        )
    return resultado