from fastapi import FastAPI

from backend.controllers import eventos_controller

tags_metadata = [
    {
        "name": "General",
        "description": "Operaciones generales de la API"
    },
    {
        "name": "Eventos",
        "description": "CRUD de eventos"
    }
]

app = FastAPI(
    title="API Eventify - 2026",
    version="1.0",
    openapi_tags=tags_metadata
)

app.include_router(eventos_controller.router)


@app.get("/", tags=["General"])
def inicio():
    return {"mensaje": "API Eventify funcionando correctamente"}