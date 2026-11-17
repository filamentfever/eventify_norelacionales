from fastapi import FastAPI

from backend.controllers import (
    eventos_controller,
    usuarios_controller,
    orden_controller,
    resenas_controller,
    dashboard_controller
)

tags_metadata = [
    {
        "name": "General",
        "description": "Operaciones generales de la API"
    },
    {
        "name": "Eventos",
        "description": "CRUD de eventos"
    },
    {
        "name": "Usuarios",
        "description": "Gestión de usuarios"
    },
    {
        "name": "Órdenes de compra",
        "description": "Consulta de órdenes de compra"
    },
    {
        "name": "Reseñas",
        "description": "Consulta de reseñas y evaluaciones"
    },
    {
        "name": "Dashboard",
        "description": "KPIs y consultas analíticas"
    }
]

app = FastAPI(
    title="API Eventify - 2026",
    version="1.0",
    openapi_tags=tags_metadata
)

app.include_router(eventos_controller.router)
app.include_router(usuarios_controller.router)
app.include_router(orden_controller.router)
app.include_router(resenas_controller.router)
app.include_router(dashboard_controller.router)


@app.get("/", tags=["General"])
def inicio():
    return {"mensaje": "API Eventify funcionando correctamente"}