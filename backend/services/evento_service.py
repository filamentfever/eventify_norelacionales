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


def _anular_ordenes(evento_oid) -> int:
    """Al cancelar un evento, sus órdenes pagadas o pendientes quedan anuladas.
    Así dejan de contar en los KPIs y en las consultas del dashboard."""
    resultado = db.ordenes_compra.update_many(
        {"evento_id": evento_oid, "estado": {"$in": ["pagada", "pendiente"]}},
        {"$set": {"estado": "anulada", "confirmado": False}}
    )
    return resultado.modified_count


def actualizar_evento(evento_id: str, evento: Evento):
    """Actualiza un evento existente. Retorna None si no existe.
    Lanza ValueError si se intenta cancelar un evento finalizado."""
    if not ObjectId.is_valid(evento_id):
        return None
    oid = ObjectId(evento_id)

    actual = db.eventos.find_one({"_id": oid}, {"estado": 1})
    if not actual:
        return None

    if actual["estado"] == "finalizado" and evento.estado == "cancelado":
        raise ValueError("No se puede cancelar un evento finalizado: forma parte del historial.")

    db.eventos.update_one({"_id": oid}, {"$set": evento.model_dump()})

    # Si se cancela por esta vía, se aplican las mismas consecuencias que en la baja
    if evento.estado == "cancelado" and actual["estado"] != "cancelado":
        _anular_ordenes(oid)

    return {"mensaje": "Evento actualizado correctamente"}


def eliminar_evento(evento_id: str):
    """Baja lógica: el evento pasa a 'cancelado' y sus órdenes se anulan.
    No se borra nada de la base. Retorna None si no existe.
    Lanza ValueError si el evento está finalizado o ya cancelado."""
    if not ObjectId.is_valid(evento_id):
        return None
    oid = ObjectId(evento_id)

    evento = db.eventos.find_one({"_id": oid}, {"estado": 1})
    if not evento:
        return None

    if evento["estado"] == "finalizado":
        raise ValueError("No se puede dar de baja un evento finalizado: forma parte del historial.")
    if evento["estado"] == "cancelado":
        raise ValueError("El evento ya está cancelado.")

    db.eventos.update_one({"_id": oid}, {"$set": {"estado": "cancelado"}})
    anuladas = _anular_ordenes(oid)

    return {
        "mensaje": "Evento dado de baja (cancelado)",
        "ordenes_anuladas": anuladas
    }