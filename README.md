# Eventify Analytics

Proyecto del Grupo 4 para la Evaluación 3 de BDY0101. Permite analizar ventas, compras y satisfacción, consultar entradas disponibles y administrar eventos.

## Arquitectura

`Streamlit + Plotly → HTTP/JSON → FastAPI → PyMongo → MongoDB Atlas`

FastAPI recibe las solicitudes en `backend/controllers`, concentra las operaciones y agregaciones en `backend/services` y valida los datos con los esquemas de `backend/models`. El backend maneja la conexión a Atlas. Streamlit consulta la API y presenta las visualizaciones y formularios en `frontend/app.py`.

## Instalación local en Windows

Clona el repositorio, abre PowerShell en la carpeta que contiene `requirements.txt` y ejecuta:

```powershell
python -m venv .venv
pip install -r requirements.txt
copy .env.example .env
```

Si ya tienes un `.env`, conserva ese archivo. Configura `MONGO_URI` con la conexión a Atlas y `DATABASE_NAME=eventify_db` si usaste el nombre del script de carga. Mantén el `.env` fuera de Git. Para ejecutar la baja transaccional, usa Atlas o un conjunto de réplicas de MongoDB. La cuenta de prueba necesita permisos de lectura y escritura en su base.

En Atlas, comprueba que la base tenga las colecciones `usuarios`, `eventos`, `ordenes_compra` y `resenas_evaluaciones`. Si debes poblar una base de demostración desde cero, usa el archivo `grupo4_eventify.mongodb.js` de la Evaluación 2 con un entorno compatible con MongoDB Playgrounds. **El script elimina y vuelve a crear esas cuatro colecciones en `eventify_db`. Úsalo solo en una base de demostración desechable.**

Con la base cargada, ejecuta cada comando en su propia terminal, desde la carpeta del proyecto:

```powershell
uvicorn backend.main:app --reload
```

```powershell
streamlit run frontend/app.py
```

Abre [Swagger](http://127.0.0.1:8000/docs) para explorar la API y el [dashboard](http://localhost:8501) para usar Streamlit. Si PyMongo muestra un error de resolución SRV, comprueba que tu red resuelva los registros del clúster. También puedes usar una cadena estándar de Atlas que empiece por `mongodb://`, con los hosts, TLS y demás opciones que indique Atlas.

## Endpoints y visualizaciones

Las rutas de la tabla usan el prefijo `/api/v1`.

| Método y ruta | Resultado |
| --- | --- |
| `GET /kpis` | Recaudación total, promedio por orden pagada y puntuación promedio. |
| `GET /consultas/compras-usuario` | Filtros opcionales `rut` y `ciudad`. Gráfico de gasto por ciudad y desglose de usuarios o detalle de compras. |
| `GET /consultas/ventas-por-evento` | Recaudación y porcentaje vendido en gráficos comparativos. Incluye eventos programados y finalizados con cero ventas. |
| `GET /consultas/eventos-futuros` | Tabla filtrada por `ciudad` y `precio_maximo`. Muestra tickets con stock y precio estrictamente menor al límite. |
| `GET /consultas/satisfaccion` | Gráfico de puntuación de eventos finalizados, cantidad de reseñas y opiniones consultables. |
| `GET, POST /eventos/` | Listado y alta de eventos. |
| `GET, PUT, DELETE /eventos/{evento_id}` | Detalle, edición y baja lógica. La baja anula órdenes pagadas y pendientes en la misma transacción. |
| `GET, POST /usuarios/` | Listado y alta de usuarios. |
| `GET /usuarios/{usuario_id}` | Detalle de un usuario. |
| `GET /ordenes/`, `GET /ordenes/{orden_id}` | Listado y detalle de órdenes. |
| `GET /resenas/`, `GET /resenas/{resena_id}` | Listado y detalle de reseñas. |

## Indicadores de negocio

- **Recaudación total.** Suma los importes de las órdenes pagadas y refleja los ingresos registrados por ventas.
- **Promedio por orden pagada.** Divide la recaudación por el número de órdenes pagadas para medir el valor medio de una compra. Una orden puede contener varias entradas.
- **Puntuación promedio.** Promedia individualmente las puntuaciones de las reseñas para medir la experiencia de los asistentes que evaluaron un evento.

## Cómo demostrar el sistema

1. Abre el dashboard y verifica las tres tarjetas de KPIs.
2. En Compras por usuario, usa el RUT precargado y selecciona Temuco. Quita el RUT para mostrar la comparación por ciudad.
3. Compara las ventas y la ocupación, busca tickets en Santiago y abre las opiniones de un evento finalizado.
4. En una base de demostración, crea un evento programado, cambia el precio de una entrada y da de baja el evento. Para demostrar el cambio en la recaudación, usa un evento de prueba que ya tenga una orden pagada. La baja conserva el evento como cancelado para efectos de historial.



[2bu34uhs]