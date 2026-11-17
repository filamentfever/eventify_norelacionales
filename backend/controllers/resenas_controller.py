from fastapi import APIRouter, HTTPException

from backend.services.resena_service import listar_resenas, obtener_resena

router = APIRouter(
    prefix="/api/v1/resenas",
    tags=["Reseñas"]
)


@router.get("/")
def obtener_resenas():
    return listar_resenas()


@router.get("/{resena_id}")
def filtro_por_id(resena_id: str):
    resultado = obtener_resena(resena_id)
    if not resultado:
        raise HTTPException(
            status_code=404,
            detail="Reseña no encontrada"
        )
    return resultado