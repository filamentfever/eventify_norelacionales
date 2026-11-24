# Eventify Analytics

Dashboard y API REST para analizar ventas, compras y satisfacción de la plataforma Eventify, consultar entradas disponibles y administrar eventos.

**Evaluación 3 · BDY0101 · Grupo 4**

Integrantes: Martina Cordova e Ignacio Retamal. 

## Arquitectura y flujo de datos

`Streamlit + Plotly → HTTP/JSON → FastAPI → PyMongo → MongoDB Atlas`

1. La persona usa el dashboard en Streamlit (`frontend/app.py`), que nunca se conecta a MongoDB.
2. Streamlit llama a la API por HTTP.
3. En FastAPI, el controller (`backend/controllers`) recibe la solicitud y valida los datos con los modelos Pydantic (`backend/models`).
4. El service (`backend/services`) ejecuta las consultas y agregaciones con PyMongo sobre Atlas.
5. La API responde JSON y Plotly lo dibuja en el dashboard.

```
eventify_norelacionales/
├── backend/
│   ├── controllers/   endpoints HTTP
│   ├── models/        esquemas Pydantic de las 4 colecciones
│   ├── services/      lógica de negocio y consultas de agregación
│   ├── database.py    conexión a Atlas
│   └── main.py        aplicación FastAPI
├── frontend/
│   └── app.py         dashboard Streamlit
├── esquema/
│   └── grupo4_eventify.mongodb.js   script de carga de la base (Evaluación 2)
├── requirements.txt
└── README.md
```

## Requisitos

- Python 3.10 o superior (el código usa anotaciones como `str | None`).
- Un cluster de MongoDB Atlas con un usuario de base de datos con permisos de lectura y escritura.
- En Atlas, tu IP actual permitida en **Network Access**. Sin esto la conexión queda colgada.

## Instalación local en Windows

Clona el repositorio, abre PowerShell en la carpeta que contiene `requirements.txt` y ejecuta:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Si PowerShell bloquea la activación del entorno (error de *Execution Policy*), permite scripts solo en esa terminal y vuelve a activarlo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\activate
```

Cuando el entorno esté activo, la línea de la terminal empieza con `(.venv)`.

Abre el `.env` y completa:

```
MONGO_URI=mongodb+srv://USUARIO:CLAVE@cluster0.xxxxx.mongodb.net/
DATABASE_NAME=eventify_db
```

## Carga de la base de datos

En Atlas, comprueba que la base tenga las colecciones `usuarios`, `eventos`, `ordenes_compra` y `resenas_evaluaciones`. Si debes poblarla desde cero, ejecuta completo el archivo `esquema/grupo4_eventify.mongodb.js` (por ejemplo con la extensión de MongoDB para VS Code o con mongosh).

**El script elimina y vuelve a crear esas cuatro colecciones en `eventify_db`. Úsalo solo en una base de demostración desechable.** También sirve para restaurar los datos originales después de probar bajas de eventos.

## Ejecución

Ejecuta cada comando en su propia terminal, desde la carpeta del proyecto y con el entorno activo:

```powershell
uvicorn backend.main:app --reload
```

```powershell
streamlit run frontend/app.py
```

Abre [Swagger](http://127.0.0.1:8000/docs) para explorar la API y el [dashboard](http://localhost:8501) para usar Streamlit. 

## Endpoints y visualizaciones

Las rutas de la tabla usan el prefijo `/api/v1`.

| Método y ruta | Resultado |
| --- | --- |
| `GET /kpis` | **KPIs.** Recaudación total, promedio por orden pagada y puntuación promedio. |
| `GET /consultas/compras-usuario` | **Consulta 1.** Filtro opcional `rut` (y `ciudad` en la API). El gráfico muestra el gasto por ciudad; la ciudad elegida en el dashboard se resalta y filtra el detalle de compras. |
| `GET /consultas/ventas-por-evento` | **Consulta 2.** Recaudación, ocupación y clasificación Exitoso / Por Mejorar. El dashboard permite filtrar por clasificación y ordenar por mayor o menor recaudación. Incluye eventos programados y finalizados con cero ventas. |
| `GET /consultas/eventos-futuros` | **Consulta 3.** Tabla filtrada por `ciudad` y `precio_maximo`. Muestra tickets con stock y precio estrictamente menor al límite. |
| `GET /consultas/satisfaccion` | **Consulta 4 (libre).** Puntuación de eventos finalizados, cantidad de reseñas y opiniones consultables. El dashboard la presenta con una dona de resumen y un filtro por nivel de satisfacción. |
| `GET, POST /eventos/` | Listado y alta de eventos. |
| `GET, PUT, DELETE /eventos/{evento_id}` | Detalle, edición y baja lógica. |
| `GET, POST /usuarios/` | Listado y alta de usuarios. |
| `GET /usuarios/{usuario_id}` | Detalle de un usuario. |
| `GET /ordenes/`, `GET /ordenes/{orden_id}` | Listado y detalle de órdenes. |
| `GET /resenas/`, `GET /resenas/{resena_id}` | Listado y detalle de reseñas. |

### Consulta 4: satisfacción de eventos finalizados

**Pregunta de negocio:** ¿qué eventos finalizados dejaron más satisfechos a los asistentes y cuáles necesitan mejoras?

Un evento se clasifica como Excelente (promedio ≥ 4.5), Bueno (≥ 3.5), Por mejorar (menos de 3.5) o Sin reseñas. La consulta usa `$lookup`, `$map`, `$switch`, `$ifNull`, `$avg`, `$size`, `$round` y `$dateToString`.

## Indicadores de negocio

- **Recaudación total.** Mide el ingreso real de la plataforma y permite evaluar su desempeño comercial. Las órdenes anuladas o pendientes no cuentan.
- **Promedio por orden pagada.** Indica cuánto gasta una persona por compra y apoya decisiones sobre precios y paquetes de entradas.
- **Puntuación promedio.** Permite detectar problemas de experiencia aunque las ventas sean buenas.

## Reglas de negocio

- **Baja lógica:** `DELETE /eventos/{id}` no borra datos. El evento pasa a `cancelado` y sus órdenes pagadas o pendientes pasan a `anulada`, todo en una sola transacción. Como los KPIs y las consultas solo cuentan órdenes pagadas, se actualizan solos y el historial se conserva.
- Un evento **finalizado** no se puede cancelar, y uno finalizado o cancelado no se puede reactivar (la API responde `409`).
- Un evento se clasifica como **Exitoso** si vendió al menos el 40 % de su stock inicial.

