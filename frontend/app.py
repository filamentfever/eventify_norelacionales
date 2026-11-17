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

    # ---- Alta
    st.subheader("➕ Agregar evento")
    with st.form("form_crear", clear_on_submit=True):
        a, b = st.columns(2)
        nombre = a.text_input("Nombre")
        codigo = b.text_input("Código lugar", "REC-TEMU-01")
        categoria = a.text_input("Categoría", "Concierto")
        estado = b.selectbox("Estado", ["programado", "finalizado", "cancelado"])
        descripcion = st.text_area("Descripción")
        fecha = a.date_input("Fecha del evento")
        hora = b.time_input("Hora")

        st.write("Recinto")
        r1, r2 = st.columns(2)
        rec_nombre = r1.text_input("Nombre del recinto")
        rec_dir = r2.text_input("Dirección")
        rec_ciudad = r1.text_input("Ciudad")
        rec_cap = r2.number_input("Capacidad", min_value=1, value=1000)
        rec_lat = r1.number_input("Latitud", value=-38.733, format="%.4f")
        rec_lon = r2.number_input("Longitud", value=-72.615, format="%.4f")

        st.write("Ticket")
        t1, t2, t3, t4 = st.columns(4)
        t_tipo = t1.text_input("Tipo", "General")
        t_precio = t2.number_input("Precio", min_value=0, value=15000, step=1000)
        t_stock = t3.number_input("Stock", min_value=0, value=100)
        t_vip = t4.checkbox("VIP")

        enviar = st.form_submit_button("Crear evento")

    if enviar:
        payload = {
            "codigo_lugar": codigo,
            "nombre": nombre,
            "categoria": categoria,
            "descripcion": descripcion,
            "fecha_evento": datetime.combine(fecha, hora).isoformat(),
            "estado": estado,
            "recinto": {
                "nombre": rec_nombre,
                "direccion": rec_dir,
                "ciudad": rec_ciudad,
                "capacidad": int(rec_cap),
                "coordenadas": {"latitud": rec_lat, "longitud": rec_lon}
            },
            "tickets_disponibles": [{
                "tipo": t_tipo,
                "precio": t_precio,
                "stock_inicial": int(t_stock),
                "stock_disponible": int(t_stock),
                "es_vip": t_vip
            }]
        }
        _, error = pedir("POST", "/eventos/", json=payload)
        if error:
            st.error(error)
        else:
            st.toast("Evento creado correctamente ✅")
            st.rerun()

    if eventos:
        opciones = {f"{e['nombre']} ({e['recinto']['ciudad']})": e["_id"] for e in eventos}

        # ---- Modificación
        st.subheader("✏️ Actualizar precios de un evento")
        elegido = st.selectbox("Evento", list(opciones.keys()), key="sel_editar")
        evento_id = opciones[elegido]
        evento, error = pedir("GET", f"/eventos/{evento_id}")

        if error:
            st.error(error)
        else:
            with st.form(f"form_editar_{evento_id}"):
                nuevos_precios = []
                for i, t in enumerate(evento["tickets_disponibles"]):
                    nuevos_precios.append(st.number_input(
                        f"Precio de {t['tipo']}", min_value=0.0,
                        value=float(t["precio"]), step=1000.0, key=f"p_{evento_id}_{i}"
                    ))
                guardar = st.form_submit_button("Guardar cambios")

            if guardar:
                evento.pop("_id")
                for t, precio in zip(evento["tickets_disponibles"], nuevos_precios):
                    t["precio"] = precio
                _, error = pedir("PUT", f"/eventos/{evento_id}", json=evento)
                if error:
                    st.error(error)
                else:
                    st.toast("Precios actualizados ✅")
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