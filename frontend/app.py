from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/api/v1"

st.set_page_config(page_title="Eventify Analytics", page_icon="🎟️", layout="wide")


def pedir(metodo, ruta, **kwargs):
    """Llama a la API. Devuelve (datos, error)."""
    try:
        r = requests.request(metodo, f"{API_URL}{ruta}", timeout=15, **kwargs)
    except requests.exceptions.ConnectionError:
        return None, "No se pudo conectar con la API. ¿Está corriendo uvicorn?"
    if r.status_code >= 400:
        try:
            detalle = r.json().get("detail", r.text)
        except ValueError:
            detalle = r.text
        return None, f"Error {r.status_code}: {detalle}"
    return r.json(), None


ESTADOS = ["programado", "finalizado", "cancelado"]
TICKET_BASE = {"tipo": "General", "precio": 15000, "stock_inicial": 100,
               "stock_disponible": 100, "es_vip": False}


def formulario_evento(prefijo, ev=None, n_tickets=1):
    """Dibuja los campos del evento (se usa dentro de un st.form).
    Devuelve (payload, errores). El envío lo decide st.form_submit_button,
    y si hay errores el evento NO se manda a la API."""
    nuevo = ev is None
    ev = ev or {}
    rec = ev.get("recinto", {})
    coord = rec.get("coordenadas", {})
    tickets = ev.get("tickets_disponibles") or [TICKET_BASE]
    errores = []

    try:
        fecha_dt = datetime.fromisoformat(str(ev["fecha_evento"]).replace("Z", ""))
    except (KeyError, ValueError):
        fecha_dt = datetime.now()
    fecha_dt = fecha_dt.replace(second=0, microsecond=0)

    estados = ESTADOS if ev.get("estado", "programado") in ESTADOS else ESTADOS + [ev["estado"]]
    k = lambda campo: f"{prefijo}_{campo}"

    a, b = st.columns(2)
    nombre = a.text_input("Nombre", ev.get("nombre", ""), key=k("nombre"))
    codigo = b.text_input("Código lugar", ev.get("codigo_lugar", "REC-TEMU-01"), key=k("codigo"))
    categoria = a.text_input("Categoría", ev.get("categoria", "Concierto"), key=k("categoria"))
    estado = b.selectbox("Estado", estados, index=estados.index(ev.get("estado", "programado")),
                         key=k("estado"))
    descripcion = st.text_area("Descripción", ev.get("descripcion", ""), key=k("descripcion"))
    fecha = a.date_input("Fecha del evento", fecha_dt.date(), key=k("fecha"))
    hora = b.time_input("Hora", fecha_dt.time(), key=k("hora"))

    st.write("Recinto")
    r1, r2 = st.columns(2)
    rec_nombre = r1.text_input("Nombre del recinto", rec.get("nombre", ""), key=k("rec_nombre"))
    rec_dir = r2.text_input("Dirección", rec.get("direccion", ""), key=k("rec_dir"))
    rec_ciudad = r1.text_input("Ciudad", rec.get("ciudad", ""), key=k("rec_ciudad"))
    rec_cap = r2.number_input("Capacidad", min_value=1, value=int(rec.get("capacidad", 1000)),
                              key=k("rec_cap"))
    rec_lat = r1.number_input("Latitud", value=float(coord.get("latitud", -38.733)),
                              format="%.4f", key=k("rec_lat"))
    rec_lon = r2.number_input("Longitud", value=float(coord.get("longitud", -72.615)),
                              format="%.4f", key=k("rec_lon"))

    st.write("Tickets")
    lista_tickets = []
    for i in range(n_tickets):
        base = tickets[i] if i < len(tickets) else TICKET_BASE
        cols = st.columns(4 if nuevo else 5)
        tipo = cols[0].text_input("Tipo", base["tipo"], key=k(f"t{i}_tipo"))
        precio = cols[1].number_input("Precio", min_value=0.0, value=float(base["precio"]),
                                      step=1000.0, key=k(f"t{i}_precio"))
        inicial = cols[2].number_input("Stock inicial", min_value=0,
                                       value=int(base["stock_inicial"]), key=k(f"t{i}_ini"))
        if nuevo:
            disponible = inicial
            vip = cols[3].checkbox("VIP", base["es_vip"], key=k(f"t{i}_vip"))
        else:
            disponible = cols[3].number_input("Stock disponible", min_value=0,
                                              value=int(base["stock_disponible"]),
                                              key=k(f"t{i}_disp"))
            vip = cols[4].checkbox("VIP", base["es_vip"], key=k(f"t{i}_vip"))
        if disponible > inicial:
            errores.append(f"Ticket {i + 1}: el stock disponible no puede superar al inicial.")
        lista_tickets.append({"tipo": tipo, "precio": precio, "stock_inicial": int(inicial),
                              "stock_disponible": int(disponible), "es_vip": vip})

    # Validación: ningún campo de texto obligatorio puede ir vacío
    obligatorios = {
        "Nombre": nombre, "Código lugar": codigo, "Categoría": categoria,
        "Descripción": descripcion, "Nombre del recinto": rec_nombre,
        "Dirección": rec_dir, "Ciudad": rec_ciudad
    }
    for etiqueta, valor in obligatorios.items():
        if not valor.strip():
            errores.append(f"{etiqueta} es obligatorio.")
    for i, t in enumerate(lista_tickets):
        if not t["tipo"].strip():
            errores.append(f"Ticket {i + 1}: el tipo es obligatorio.")

    payload = {
        "codigo_lugar": codigo,
        "nombre": nombre,
        "categoria": categoria,
        "descripcion": descripcion,
        "fecha_evento": datetime.combine(fecha, hora).isoformat(),
        "estado": estado,
        "recinto": {
            "nombre": rec_nombre, "direccion": rec_dir, "ciudad": rec_ciudad,
            "capacidad": int(rec_cap),
            "coordenadas": {"latitud": rec_lat, "longitud": rec_lon}
        },
        "tickets_disponibles": lista_tickets
    }
    return payload, errores


st.title("🎟️ Eventify Analytics")

# ---------------------------------------------------------------- KPIs
kpis, error = pedir("GET", "/kpis")
if error:
    st.error(error)
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Recaudación total", f"${kpis['recaudacion_total']:,.0f}")
c2.metric("Ticket promedio por orden", f"${kpis['ticket_promedio']:,.0f}")
c3.metric("Puntuación promedio", f"⭐ {kpis['puntuacion_promedio']}")

st.divider()

# Lista de eventos (sirve para los filtros y para el panel de administración)
eventos, error = pedir("GET", "/eventos/")
if error:
    st.error(error)
    eventos = []
ciudades = sorted({e["recinto"]["ciudad"] for e in eventos})

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1️⃣ Compras por usuario",
    "2️⃣ Ventas por evento",
    "3️⃣ Eventos futuros",
    "4️⃣ Satisfacción",
    "🛠️ Administración"
])

# ---------------------------------------------------- Consulta 1
with tab1:
    st.subheader("Gasto por ciudad y detalle de compras")
    col_a, col_b = st.columns(2)
    rut = col_a.text_input("RUT del usuario (vacío = todos los usuarios)", "10754246-2")
    ciudad_sel = col_b.selectbox("Ciudad", ["Todas"] + ciudades, key="c1_ciudad")

    params = {}
    if rut.strip():
        params["rut"] = rut.strip()
    if ciudad_sel != "Todas":
        params["ciudad"] = ciudad_sel

    datos, error = pedir("GET", "/consultas/compras-usuario", params=params)
    if error:
        st.error(error)
    else:
        df_gasto = pd.DataFrame(datos["gasto_por_ciudad"])
        if df_gasto.empty:
            st.info("No hay compras pagadas con esos filtros.")
        else:
            por_ciudad = df_gasto.groupby("ciudad", as_index=False)["gasto_total"].sum()
            fig = px.bar(por_ciudad, x="ciudad", y="gasto_total", text_auto=".3s",
                         title="Gasto total por ciudad", labels={"gasto_total": "Gasto total ($)"})
            st.plotly_chart(fig, use_container_width=True)

            if datos["detalle"]:
                st.write("Detalle de compras")
                st.dataframe(pd.DataFrame(datos["detalle"]), use_container_width=True)

# ---------------------------------------------------- Consulta 2
with tab2:
    st.subheader("Recaudación y ocupación por evento")
    datos, error = pedir("GET", "/consultas/ventas-por-evento")
    if error:
        st.error(error)
    elif datos:
        df = pd.DataFrame(datos)
        colores = {"Exitoso": "#2ca02c", "Por Mejorar": "#d62728"}

        fig1 = px.bar(df, x="evento", y="total_recaudado", color="etiqueta",
                      color_discrete_map=colores, title="Total recaudado por evento",
                      labels={"total_recaudado": "Recaudado ($)"})
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.bar(df, x="evento", y="porcentaje_venta", color="etiqueta",
                      color_discrete_map=colores, title="Ocupación (% del stock inicial vendido)",
                      labels={"porcentaje_venta": "% vendido"})
        fig2.add_hline(y=40, line_dash="dash", annotation_text="Umbral 'Exitoso' (40%)")
        st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(df, use_container_width=True)

# ---------------------------------------------------- Consulta 3
with tab3:
    st.subheader("Eventos futuros con tickets disponibles")
    col_a, col_b = st.columns(2)
    ciudad_f = col_a.selectbox("Ciudad", ciudades, key="c3_ciudad") if ciudades else None
    precio_max = col_b.slider("Precio máximo del ticket ($)", 0, 100000, 20000, step=1000)

    if ciudad_f:
        datos, error = pedir("GET", "/consultas/eventos-futuros",
                             params={"ciudad": ciudad_f, "precio_maximo": precio_max})
        if error:
            st.error(error)
        elif not datos:
            st.info("No hay eventos futuros con tickets bajo ese precio en esa ciudad.")
        else:
            st.dataframe(pd.DataFrame(datos), use_container_width=True)

# ---------------------------------------------------- Consulta 4
with tab4:
    st.subheader("Satisfacción de los eventos finalizados")
    datos, error = pedir("GET", "/consultas/satisfaccion")
    if error:
        st.error(error)
    elif datos:
        df = pd.DataFrame(datos)
        fig = px.bar(df, x="evento", y="promedio_puntuacion", color="valoracion",
                     hover_data=["total_resenas", "ciudad", "categoria"],
                     title="Puntuación promedio por evento",
                     labels={"promedio_puntuacion": "Puntuación promedio"})
        fig.update_yaxes(range=[0, 5])
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True)

# ---------------------------------------------------- Administración
with tab5:
    st.subheader("Eventos registrados")
    if eventos:
        tabla = pd.DataFrame([{
            "nombre": e["nombre"],
            "categoria": e["categoria"],
            "ciudad": e["recinto"]["ciudad"],
            "estado": e["estado"],
            "fecha_evento": e["fecha_evento"],
            "_id": e["_id"]
        } for e in eventos])
        st.dataframe(tabla, use_container_width=True)

    # ---- Alta (st.form + validación: un evento incompleto nunca se envía)
    st.subheader("➕ Agregar evento")
    n_crear = st.session_state.setdefault("n_crear", 0)  # cambia al crear → limpia el formulario

    # Este selector va FUERA del st.form para que los campos de tickets se actualicen al instante
    n_tickets = st.number_input("Cantidad de tipos de ticket", min_value=1, max_value=10,
                                value=1, key=f"crear{n_crear}_n_tickets")

    with st.form(f"form_crear_{n_crear}"):
        payload, errores = formulario_evento(f"crear{n_crear}", n_tickets=int(n_tickets))
        enviar = st.form_submit_button("Crear evento")

    if enviar:
        if errores:
            for msg in errores:
                st.error(msg)
        else:
            _, error = pedir("POST", "/eventos/", json=payload)
            if error:
                st.error(error)
            else:
                st.session_state["n_crear"] += 1
                st.toast("Evento creado correctamente ✅")
                st.rerun()

    if eventos:
        opciones = {f"{e['nombre']} ({e['recinto']['ciudad']})": e["_id"] for e in eventos}

        # ---- Modificación (evento completo)
        st.subheader("✏️ Modificar evento")
        elegido = st.selectbox("Evento", list(opciones.keys()), key="sel_editar")
        evento_id = opciones[elegido]
        evento, error = pedir("GET", f"/eventos/{evento_id}")

        if error:
            st.error(error)
        else:
            n_tickets_ed = st.number_input("Cantidad de tipos de ticket", min_value=1, max_value=10,
                                           value=len(evento["tickets_disponibles"]),
                                           key=f"editar_{evento_id}_n_tickets")

            with st.form(f"form_editar_{evento_id}"):
                payload_ed, errores_ed = formulario_evento(
                    f"editar_{evento_id}", evento, int(n_tickets_ed))
                guardar = st.form_submit_button("Guardar cambios")

            if guardar:
                if errores_ed:
                    for msg in errores_ed:
                        st.error(msg)
                else:
                    _, error = pedir("PUT", f"/eventos/{evento_id}", json=payload_ed)
                    if error:
                        st.error(error)
                    else:
                        st.toast("Evento actualizado ✅")
                        st.rerun()

        # ---- Baja
        st.subheader("🗑️ Eliminar evento")
        st.caption("Ojo: elimina solo eventos de prueba. Los eventos con órdenes de compra "
                   "dejarían esas órdenes sin evento.")
        a_borrar = st.selectbox("Evento a eliminar", list(opciones.keys()), key="sel_borrar")
        if st.button("Eliminar"):
            _, error = pedir("DELETE", f"/eventos/{opciones[a_borrar]}")
            if error:
                st.error(error)
            else:
                st.toast("Evento eliminado ✅")
                st.rerun()