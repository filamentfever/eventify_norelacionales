from bson import ObjectId

from backend.database import db
from backend.models.usuario import Usuario


def serializar_documento(documento):
    """Convierte el _id (ObjectId) en texto para poder devolverlo como JSON."""
    if documento:
        documento["_id"] = str(documento["_id"])
    return documento


def listar_usuarios():
    """Obtiene todos los usuarios"""
    return [serializar_documento(u) for u in db.usuarios.find()]


def obtener_usuario(usuario_id: str):
    """Obtiene un usuario por su _id. Retorna None si no existe."""
    if not ObjectId.is_valid(usuario_id):
        return None
    return serializar_documento(db.usuarios.find_one({"_id": ObjectId(usuario_id)}))


def agregar_usuario(usuario: Usuario) -> dict:
    """Agrega un nuevo usuario"""
    resultado = db.usuarios.insert_one(usuario.model_dump())
    return {
        "mensaje": "Usuario agregado correctamente",
        "id": str(resultado.inserted_id)
    }