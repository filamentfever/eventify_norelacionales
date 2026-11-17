from datetime import datetime

from backend.database import db


class DashboardService:

    @staticmethod
    def obtener_kpis():
        """3 KPIs: recaudación total, ticket promedio y puntuación promedio."""
        ventas = list(db.ordenes_compra.aggregate([
            {"$match": {"estado": "pagada"}},
            {
                "$group": {
                    "_id": None,
                    "recaudacion_total": {"$sum": "$total"},
                    "ticket_promedio": {"$avg": "$total"},
                    "ordenes_pagadas": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "recaudacion_total": 1,
                    "ticket_promedio": {"$round": ["$ticket_promedio", 0]},
                    "ordenes_pagadas": 1
                }
            }
        ]))

        satisfaccion = list(db.resenas_evaluaciones.aggregate([
            {
                "$group": {
                    "_id": None,
                    "puntuacion_promedio": {"$avg": "$puntuacion"},
                    "total_resenas": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "puntuacion_promedio": {"$round": ["$puntuacion_promedio", 2]},
                    "total_resenas": 1
                }
            }
        ]))

        kpis = {
            "recaudacion_total": 0,
            "ticket_promedio": 0,
            "ordenes_pagadas": 0,
            "puntuacion_promedio": 0,
            "total_resenas": 0
        }
        if ventas:
            kpis.update(ventas[0])
        if satisfaccion:
            kpis.update(satisfaccion[0])
        return kpis

    @staticmethod
    def compras_usuario(rut: str | None, ciudad: str | None):
        """Consulta 1: detalle de compras y gasto total por ciudad."""
        filtro = {"estado": "pagada"}

        if rut:
            usuario = db.usuarios.find_one({"rut": rut})
            if not usuario:
                return None
            filtro["usuario_id"] = usuario["_id"]

        base = [
            {"$match": filtro},
            {
                "$lookup": {
                    "from": "eventos",
                    "localField": "evento_id",
                    "foreignField": "_id",
                    "as": "evento"
                }
            },
            {"$unwind": "$evento"}
        ]

        if ciudad:
            base.append({"$match": {"evento.recinto.ciudad": ciudad}})

        base += [
            {
                "$lookup": {
                    "from": "usuarios",
                    "localField": "usuario_id",
                    "foreignField": "_id",
                    "as": "usuario"
                }
            },
            {"$unwind": "$usuario"}
        ]

        gasto = list(db.ordenes_compra.aggregate(base + [
            {
                "$group": {
                    "_id": {
                        "rut": "$usuario.rut",
                        "nombre": "$usuario.nombre",
                        "ciudad": "$evento.recinto.ciudad"
                    },
                    "gasto_total": {"$sum": "$total"},
                    "ordenes_pagadas": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "rut": "$_id.rut",
                    "nombre": "$_id.nombre",
                    "ciudad": "$_id.ciudad",
                    "gasto_total": 1,
                    "ordenes_pagadas": 1
                }
            }
        ]))

        # El detalle ítem por ítem solo se entrega cuando se pide un usuario
        detalle = []
        if rut:
            detalle = list(db.ordenes_compra.aggregate(base + [
                {"$unwind": "$items"},
                {
                    "$project": {
                        "_id": 0,
                        "rut": "$usuario.rut",
                        "nombre": "$usuario.nombre",
                        "fecha_compra": 1,
                        "evento": "$evento.nombre",
                        "ciudad": "$evento.recinto.ciudad",
                        "tipo_ticket": "$items.tipo_ticket",
                        "cantidad": "$items.cantidad",
                        "precio_unitario": "$items.precio_unitario"
                    }
                }
            ]))

        return {"detalle": detalle, "gasto_por_ciudad": gasto}

    @staticmethod
    def ventas_por_evento():
        """Consulta 2: recaudación, ocupación y clasificación por evento."""
        return list(db.ordenes_compra.aggregate([
            {"$match": {"estado": "pagada"}},
            {
                "$project": {
                    "evento_id": 1,
                    "total": 1,
                    "tickets_orden": {"$sum": "$items.cantidad"}
                }
            },
            {
                "$group": {
                    "_id": "$evento_id",
                    "total_recaudado": {"$sum": "$total"},
                    "tickets_vendidos": {"$sum": "$tickets_orden"}
                }
            },
            {
                "$lookup": {
                    "from": "eventos",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "evento"
                }
            },
            {"$unwind": "$evento"},
            {
                "$project": {
                    "_id": 0,
                    "evento": "$evento.nombre",
                    "ciudad": "$evento.recinto.ciudad",
                    "estado_evento": "$evento.estado",
                    "total_recaudado": 1,
                    "tickets_vendidos": 1,
                    "stock_inicial_total": {"$sum": "$evento.tickets_disponibles.stock_inicial"}
                }
            },
            {
                "$project": {
                    "evento": 1,
                    "ciudad": 1,
                    "estado_evento": 1,
                    "total_recaudado": 1,
                    "tickets_vendidos": 1,
                    "stock_inicial_total": 1,
                    "porcentaje_venta": {
                        "$round": [
                            {"$multiply": [
                                {"$divide": ["$tickets_vendidos", "$stock_inicial_total"]},
                                100
                            ]},
                            1
                        ]
                    }
                }
            },
            {
                "$project": {
                    "evento": 1,
                    "ciudad": 1,
                    "estado_evento": 1,
                    "total_recaudado": 1,
                    "tickets_vendidos": 1,
                    "stock_inicial_total": 1,
                    "porcentaje_venta": 1,
                    "etiqueta": {
                        "$cond": [{"$gte": ["$porcentaje_venta", 40]}, "Exitoso", "Por Mejorar"]
                    }
                }
            },
            {"$sort": {"total_recaudado": -1}}
        ]))

    @staticmethod
    def eventos_futuros(ciudad: str, precio_maximo: float):
        """Consulta 3: eventos futuros en una ciudad con tickets baratos."""
        return list(db.eventos.aggregate([
            {
                "$match": {
                    "recinto.ciudad": ciudad,
                    "fecha_evento": {"$gt": datetime.now()},
                    "estado": "programado"
                }
            },
            {"$unwind": "$tickets_disponibles"},
            {
                "$match": {
                    "tickets_disponibles.precio": {"$lt": precio_maximo},
                    "tickets_disponibles.stock_disponible": {"$gt": 0}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "evento": "$nombre",
                    "fecha_evento": 1,
                    "ciudad": "$recinto.ciudad",
                    "tipo_ticket": "$tickets_disponibles.tipo",
                    "precio": "$tickets_disponibles.precio",
                    "stock_disponible": "$tickets_disponibles.stock_disponible"
                }
            },
            {"$sort": {"fecha_evento": 1}}
        ]))

    @staticmethod
    def satisfaccion_eventos():
        """Consulta 4 (libre): nivel de satisfacción de eventos finalizados."""
        return list(db.eventos.aggregate([
            {"$match": {"estado": "finalizado"}},
            {
                "$lookup": {
                    "from": "resenas_evaluaciones",
                    "localField": "_id",
                    "foreignField": "evento_id",
                    "as": "resenas"
                }
            },
            {
                "$project": {
                    "nombre": 1,
                    "categoria": 1,
                    "recinto": 1,
                    "fecha_evento": 1,
                    "total_resenas": {"$size": "$resenas"},
                    "promedio_puntuacion": {
                        "$round": [{"$ifNull": [{"$avg": "$resenas.puntuacion"}, 0]}, 1]
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "evento": "$nombre",
                    "ciudad": "$recinto.ciudad",
                    "categoria": 1,
                    "fecha": {"$dateToString": {"format": "%d-%m-%Y", "date": "$fecha_evento"}},
                    "total_resenas": 1,
                    "promedio_puntuacion": 1,
                    "valoracion": {
                        "$switch": {
                            "branches": [
                                {"case": {"$eq": ["$total_resenas", 0]}, "then": "Sin reseñas"},
                                {"case": {"$gte": ["$promedio_puntuacion", 4.5]}, "then": "Excelente"},
                                {"case": {"$gte": ["$promedio_puntuacion", 3.5]}, "then": "Bueno"}
                            ],
                            "default": "Por mejorar"
                        }
                    }
                }
            },
            {"$sort": {"promedio_puntuacion": -1}}
        ]))