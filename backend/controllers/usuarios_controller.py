from fastapi import APIRouter, HTTPException

from backend.models.usuario import Usuario
from backend.services.usuario_service import (
    listar_usuarios,
    obtener_usuario,
    agregar_usuario
)

router = APIRouter(
    prefix="/api/v1/usuarios",
    tags=["Usuarios"]
)


@router.get("/")
def obtener_usuarios():
    return listar_usuarios()


@router.get("/{usuario_id}")
def filtro_por_id(usuario_id: str):
    resultado = obtener_usuario(usuario_id)
    if not resultado:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )
    return resultado


@router.post("/", status_code=201)
def crear_usuario(usuario: Usuario):
    return agregar_usuario(usuario)