from bson import ObjectId

from backend.database import db


def serializar_resena(documento):
    """Convierte los ObjectId (_id, usuario_id, evento_id) en texto."""
    if documento:
        documento["_id"] = str(documento["_id"])
        documento["usuario_id"] = str(documento["usuario_id"])
        documento["evento_id"] = str(documento["evento_id"])
    return documento


def listar_resenas():
    """Obtiene todas las reseñas"""
    return [serializar_resena(r) for r in db.resenas_evaluaciones.find()]


def obtener_resena(resena_id: str):
    """Obtiene una reseña por su _id. Retorna None si no existe."""
    if not ObjectId.is_valid(resena_id):
        return None
    return serializar_resena(db.resenas_evaluaciones.find_one({"_id": ObjectId(resena_id)}))