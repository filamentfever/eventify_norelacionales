from fastapi import APIRouter, HTTPException

from backend.services.dashboard_service import DashboardService

router = APIRouter(
    prefix="/api/v1",
    tags=["Dashboard"]
)


@router.get("/kpis")
def obtener_kpis():
    return DashboardService.obtener_kpis()


@router.get("/consultas/compras-usuario")
def compras_usuario(rut: str | None = None, ciudad: str | None = None):
    resultado = DashboardService.compras_usuario(rut, ciudad)
    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )
    return resultado


@router.get("/consultas/ventas-por-evento")
def ventas_por_evento():
    return DashboardService.ventas_por_evento()


@router.get("/consultas/eventos-futuros")
def eventos_futuros(ciudad: str, precio_maximo: float = 20000):
    return DashboardService.eventos_futuros(ciudad, precio_maximo)


@router.get("/consultas/satisfaccion")
def satisfaccion_eventos():
    return DashboardService.satisfaccion_eventos()