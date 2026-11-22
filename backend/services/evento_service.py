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


def _cancelar_evento(evento_oid, cambios=None):
    """Cancela el evento y anula sus órdenes en una transacción de MongoDB."""
    def cancelar(session):
        actual = db.eventos.find_one({"_id": evento_oid}, {"estado": 1}, session=session)
        if not actual:
            return None
        if actual["estado"] == "finalizado":
            raise ValueError("No se puede cancelar un evento finalizado.")
        if actual["estado"] == "cancelado" and cambios is None:
            raise ValueError("El evento ya está cancelado.")

        db.eventos.update_one(
            {"_id": evento_oid},
            {"$set": {**(cambios or {}), "estado": "cancelado"}},
            session=session
        )
        ordenes = db.ordenes_compra.update_many(
            {"evento_id": evento_oid, "estado": {"$in": ["pagada", "pendiente"]}},
            {"$set": {"estado": "anulada", "confirmado": False}},
            session=session
        )
        return ordenes.modified_count

    with db.client.start_session() as session:
        return session.with_transaction(cancelar)


def actualizar_evento(evento_id: str, evento: Evento):
    if not ObjectId.is_valid(evento_id):
        return None
    oid = ObjectId(evento_id)
    cambios = evento.model_dump()

    if evento.estado == "cancelado":
        anuladas = _cancelar_evento(oid, cambios)
        if anuladas is None:
            return None
        return {"mensaje": "Evento actualizado correctamente", "ordenes_anuladas": anuladas}

    estados_editables = ["programado", "finalizado"] if evento.estado == "finalizado" else ["programado"]
    resultado = db.eventos.update_one(
        {"_id": oid, "estado": {"$in": estados_editables}},
        {"$set": cambios}
    )
    if resultado.matched_count == 0:
        if not db.eventos.find_one({"_id": oid}, {"_id": 1}):
            return None
        raise ValueError("Un evento finalizado o cancelado no se puede reactivar.")

    return {"mensaje": "Evento actualizado correctamente"}


def eliminar_evento(evento_id: str):
    if not ObjectId.is_valid(evento_id):
        return None

    anuladas = _cancelar_evento(ObjectId(evento_id))
    if anuladas is None:
        return None

    return {
        "mensaje": "Evento dado de baja (cancelado)",
        "ordenes_anuladas": anuladas
    }
