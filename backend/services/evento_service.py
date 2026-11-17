from bson import ObjectId

from backend.database import db
from backend.models.evento import Evento


def serializar_documento(documento):
    """Convierte el _id (ObjectId) en texto para poder devolverlo como JSON."""
    if documento:
        documento["_id"] = str(documento["_id"])
    return documento


def serializar_lista(documentos):
    return [serializar_documento(documento) for documento in documentos]


def listar_eventos():
    """Obtiene todos los eventos"""
    return serializar_lista(db.eventos.find())


def obtener_evento(evento_id: str):
    """Obtiene un evento por su _id. Retorna None si no existe."""
    if not ObjectId.is_valid(evento_id):
        return None
    return serializar_documento(db.eventos.find_one({"_id": ObjectId(evento_id)}))


def agregar_evento(evento: Evento) -> dict:
    """Agrega un nuevo evento"""
    resultado = db.eventos.insert_one(evento.model_dump())
    return {
        "mensaje": "Evento agregado correctamente",
        "id": str(resultado.inserted_id)
    }


def actualizar_evento(evento_id: str, evento: Evento):
    """Actualiza un evento existente. Retorna None si no existe."""
    if not ObjectId.is_valid(evento_id):
        return None
    resultado = db.eventos.update_one(
        {"_id": ObjectId(evento_id)},
        {"$set": evento.model_dump()}
    )
    if resultado.matched_count == 0:
        return None
    return {"mensaje": "Evento actualizado correctamente"}


def eliminar_evento(evento_id: str):
    """Elimina un evento. Retorna None si no existe."""
    if not ObjectId.is_valid(evento_id):
        return None
    resultado = db.eventos.delete_one({"_id": ObjectId(evento_id)})
    if resultado.deleted_count == 0:
        return None
    return {"mensaje": "Evento eliminado correctamente"}