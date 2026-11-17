from fastapi import APIRouter, HTTPException

from backend.models.evento import Evento
from backend.services.evento_service import (
    listar_eventos,
    obtener_evento,
    agregar_evento,
    actualizar_evento,
    eliminar_evento
)

router = APIRouter(
    prefix="/api/v1/eventos",
    tags=["Eventos"]
)


@router.get("/")
def obtener_eventos():
    return listar_eventos()


@router.get("/{evento_id}")
def filtro_por_id(evento_id: str):
    resultado = obtener_evento(evento_id)
    if not resultado:
        raise HTTPException(
            status_code=404,
            detail="Evento no encontrado"
        )
    return resultado


@router.post("/", status_code=201)
def crear_evento(evento: Evento):
    return agregar_evento(evento)


@router.put("/{evento_id}")
def modificar_evento(evento_id: str, evento: Evento):
    resultado = actualizar_evento(evento_id, evento)
    if not resultado:
        raise HTTPException(
            status_code=404,
            detail="Evento no encontrado"
        )
    return resultado


@router.delete("/{evento_id}")
def borrar_evento(evento_id: str):
    resultado = eliminar_evento(evento_id)
    if not resultado:
        raise HTTPException(
            status_code=404,
            detail="Evento no encontrado"
        )
    return resultado