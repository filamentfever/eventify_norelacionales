from bson import ObjectId

from backend.database import db


def serializar_orden(documento):
    """Convierte los ObjectId (_id, usuario_id, evento_id) en texto."""
    if documento:
        documento["_id"] = str(documento["_id"])
        documento["usuario_id"] = str(documento["usuario_id"])
        documento["evento_id"] = str(documento["evento_id"])
    return documento


def listar_ordenes():
    """Obtiene todas las órdenes de compra"""
    return [serializar_orden(o) for o in db.ordenes_compra.find()]


def obtener_orden(orden_id: str):
    """Obtiene una orden por su _id. Retorna None si no existe."""
    if not ObjectId.is_valid(orden_id):
        return None
    return serializar_orden(db.ordenes_compra.find_one({"_id": ObjectId(orden_id)}))