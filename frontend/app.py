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
    except requests.exceptions.Timeout:
        return None, "La API tardó demasiado en responder. Revisa el estado antes de repetir la operación."
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

    estado_actual = ev.get("estado", "programado")
    estados = {
        "finalizado": ["finalizado"],
        "cancelado": ["cancelado"]
    }.get(estado_actual, ESTADOS if estado_actual in ESTADOS else ESTADOS + [estado_actual])
    k = lambda campo: f"{prefijo}_{campo}"

    a, b = st.columns(2)
    nombre = a.text_input("Nombre", ev.get("nombre", ""), key=k("nombre"))
    codigo = b.text_input("Código lugar", ev.get("codigo_lugar", "REC-TEMU-01"), key=k("codigo"))
    categoria = a.text_input("Categoría", ev.get("categoria", "Concierto"), key=k("categoria"))
    estado = b.selectbox("Estado", estados, index=estados.index(estado_actual),
                         key=k("estado"), disabled=len(estados) == 1)
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
    ciudad_sel = col_b.selectbox("Ciudad (resalta en el gráfico y filtra el detalle)",
                                 ["Todas"] + ciudades, key="c1_ciudad")

    # La ciudad NO se envía a la API: así el gráfico siempre muestra la distribución completa
    params = {"rut": rut.strip()} if rut.strip() else {}
    datos, error = pedir("GET", "/consultas/compras-usuario", params=params)
    if error:
        st.error(error)
    else:
        df_gasto = pd.DataFrame(datos["gasto_por_ciudad"])
        if df_gasto.empty:
            st.info("No hay compras pagadas para ese usuario.")
        else:
            por_ciudad = (df_gasto.groupby("ciudad", as_index=False)["gasto_total"].sum()
                          .sort_values("gasto_total", ascending=False))

            if len(por_ciudad) == 1:
                # Una sola ciudad: una barra aislada no aporta, se muestra como indicador
                fila = por_ciudad.iloc[0]
                st.metric(f"Gasto total en {fila['ciudad']}", f"${fila['gasto_total']:,.0f}")
            else:
                if ciudad_sel == "Todas":
                    fig = px.bar(por_ciudad, x="ciudad", y="gasto_total", text="gasto_total",
                                 title="Gasto total por ciudad",
                                 labels={"gasto_total": "Gasto total ($)", "ciudad": "Ciudad"})
                else:
                    por_ciudad["Selección"] = por_ciudad["ciudad"].apply(
                        lambda c: "Seleccionada" if c == ciudad_sel else "Otras ciudades")
                    fig = px.bar(por_ciudad, x="ciudad", y="gasto_total", text="gasto_total",
                                 color="Selección",
                                 color_discrete_map={"Seleccionada": "#1f77b4",
                                                     "Otras ciudades": "#7f7f7f"},
                                 title="Gasto total por ciudad",
                                 labels={"gasto_total": "Gasto total ($)", "ciudad": "Ciudad"})
                fig.update_traces(texttemplate="$%{y:,.0f}", textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

            if not rut.strip():
                with st.expander("Desglose por usuario y ciudad"):
                    desglose = df_gasto if ciudad_sel == "Todas" else df_gasto[df_gasto["ciudad"] == ciudad_sel]
                    st.dataframe(desglose, use_container_width=True, hide_index=True)

            detalle = pd.DataFrame(datos["detalle"])
            if not detalle.empty:
                if ciudad_sel != "Todas":
                    detalle = detalle[detalle["ciudad"] == ciudad_sel]
                st.write("Detalle de compras")
                if detalle.empty:
                    st.info("Este usuario no tiene compras pagadas en esa ciudad.")
                else:
                    st.dataframe(detalle, use_container_width=True, hide_index=True)

# ---------------------------------------------------- Consulta 2
with tab2:
    st.subheader("Recaudación y ocupación por evento")
    datos, error = pedir("GET", "/consultas/ventas-por-evento")
    if error:
        st.error(error)
    elif datos:
        df = pd.DataFrame(datos)
        colores = {"Exitoso": "#2ca02c", "Por Mejorar": "#d62728"}

        # Resumen general (siempre sobre todos los eventos)
        exitosos = int((df["etiqueta"] == "Exitoso").sum())
        m1, m2, m3 = st.columns(3)
        m1.metric("Eventos evaluados", len(df))
        m2.metric("Exitosos (≥ 40% vendido)", exitosos)
        m3.metric("Por mejorar", len(df) - exitosos)

        # Controles: qué clasificación ver y desde qué extremo de la recaudación
        f1, f2 = st.columns(2)
        clasificacion = f1.radio("Clasificación", ["Todos", "Exitoso", "Por Mejorar"],
                                 horizontal=True, key="c2_clasificacion")
        orden = f2.radio("Ordenar por recaudación", ["Mayor recaudación", "Menor recaudación"],
                         horizontal=True, key="c2_orden")
        mayor = orden == "Mayor recaudación"

        df_f = df if clasificacion == "Todos" else df[df["etiqueta"] == clasificacion]
        df_f = df_f.sort_values(["total_recaudado", "evento"], ascending=[not mayor, True])

        if df_f.empty:
            st.info("No hay eventos con esa clasificación.")
        else:
            if len(df_f) > 5:
                top = st.slider("Cantidad de eventos a mostrar", 5, len(df_f), min(10, len(df_f)))
            else:
                top = len(df_f)
            df_top = df_f.head(top)
            orden_eventos = df_top["evento"].tolist()  # de arriba hacia abajo

            criterio = "mayor" if mayor else "menor"
            sufijo = "" if clasificacion == "Todos" else f" · {clasificacion}"
            st.caption(f"Mostrando {top} de {len(df_f)} eventos, ordenados de {criterio} a "
                       f"{'menor' if mayor else 'mayor'} recaudación.")

            def formatear(fig):
                """Mismo orden vertical en ambos gráficos y barras alineadas."""
                fig.update_yaxes(categoryorder="array", categoryarray=orden_eventos,
                                 autorange="reversed")
                fig.update_traces(offsetgroup="barras", textposition="outside", cliponaxis=False)
                fig.update_layout(barmode="overlay", legend_title_text="",
                                  height=max(350, 45 * top))

            fig1 = px.bar(df_top, x="total_recaudado", y="evento", orientation="h",
                          color="etiqueta", color_discrete_map=colores,
                          text="total_recaudado",
                          hover_data=["ciudad", "tickets_vendidos", "porcentaje_venta"],
                          title=f"{top} eventos con {criterio} recaudación{sufijo}",
                          labels={"total_recaudado": "Recaudado ($)", "evento": "",
                                  "etiqueta": "Clasificación"})
            fig1.update_traces(texttemplate="$%{x:,.0f}")
            formatear(fig1)
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = px.bar(df_top, x="porcentaje_venta", y="evento", orientation="h",
                          color="etiqueta", color_discrete_map=colores,
                          text="porcentaje_venta",
                          hover_data=["ciudad", "tickets_vendidos", "stock_inicial_total"],
                          title="Ocupación de esos eventos (% del stock inicial vendido)",
                          labels={"porcentaje_venta": "% vendido", "evento": "",
                                  "etiqueta": "Clasificación"})
            fig2.update_traces(texttemplate="%{x}%")
            fig2.add_vline(x=40, line_dash="dash", line_color="#ff9f1c", line_width=2)
            fig2.update_xaxes(title_text="% vendido (la línea punteada marca el umbral 'Exitoso': 40%)")
            formatear(fig2)
            fig2.update_layout(xaxis_range=[0, max(100, df_top["porcentaje_venta"].max() * 1.1)])
            st.plotly_chart(fig2, use_container_width=True)

            st.write("Detalle")
            st.dataframe(
                df_f, use_container_width=True, hide_index=True,
                column_config={
                    "total_recaudado": st.column_config.NumberColumn("Recaudado", format="$%d"),
                    "porcentaje_venta": st.column_config.NumberColumn("% vendido", format="%.1f"),
                }
            )

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
        orden = ["Excelente", "Bueno", "Por mejorar", "Sin reseñas"]
        colores_val = {"Excelente": "#2ca02c", "Bueno": "#1f77b4",
                       "Por mejorar": "#d62728", "Sin reseñas": "#7f7f7f"}

        # Resumen: cuántos eventos hay en cada nivel de satisfacción
        resumen = (df["valoracion"].value_counts().reindex(orden).dropna().astype(int)
                   .rename_axis("valoracion").reset_index(name="eventos"))

        col_resumen, col_detalle = st.columns([1, 2])

        with col_resumen:
            fig_dona = px.pie(resumen, names="valoracion", values="eventos", hole=0.5,
                              color="valoracion", color_discrete_map=colores_val,
                              title="Eventos por nivel de satisfacción")
            fig_dona.update_traces(textinfo="value+percent", sort=False)
            fig_dona.update_layout(legend_title_text="")
            st.plotly_chart(fig_dona, use_container_width=True)

        with col_detalle:
            # "Sin reseñas" no tiene puntuación que comparar, por eso no se ofrece como filtro
            niveles_con_resenas = [n for n in orden[:3] if n in resumen["valoracion"].values]
            niveles = st.multiselect("Filtrar por nivel de satisfacción",
                                     niveles_con_resenas, default=niveles_con_resenas)
            df_f = df[df["valoracion"].isin(niveles)]

            if df_f.empty:
                st.info("Selecciona al menos un nivel de satisfacción.")
            else:
                fig = px.bar(df_f, x="promedio_puntuacion", y="evento", orientation="h",
                             color="valoracion", color_discrete_map=colores_val,
                             text="promedio_puntuacion",
                             hover_data=["total_resenas", "ciudad", "categoria"],
                             title="Puntuación promedio por evento",
                             labels={"promedio_puntuacion": "Puntuación promedio",
                                     "evento": "", "valoracion": "Valoración"})
                fig.update_traces(textposition="outside", cliponaxis=False)
                fig.update_layout(yaxis={"categoryorder": "total ascending"},
                                  xaxis_range=[0, 5.5], legend_title_text="",
                                  height=max(300, 32 * len(df_f)))
                st.plotly_chart(fig, use_container_width=True)

        if not df_f.empty:
            st.dataframe(df_f.drop(columns="opiniones"), use_container_width=True, hide_index=True)
            seleccion = st.selectbox(
                "Opiniones de un evento",
                options=df_f.index,
                format_func=lambda i: f"{df_f.at[i, 'evento']} · {df_f.at[i, 'ciudad']} · {df_f.at[i, 'fecha']}"
            )
            opiniones = df_f.at[seleccion, "opiniones"]
            if opiniones:
                st.dataframe(pd.DataFrame(opiniones), use_container_width=True, hide_index=True)
            else:
                st.info("Este evento todavía no tiene reseñas.")
    else:
        st.info("Todavía no hay eventos finalizados.")

# ---------------------------------------------------- Administración
with tab5:
    st.subheader("Eventos registrados")
    if eventos:
        tabla = pd.DataFrame([{
            "Nombre": e["nombre"],
            "Categoría": e["categoria"],
            "Ciudad": e["recinto"]["ciudad"],
            "Estado": e["estado"],
            "Fecha": e["fecha_evento"][:16].replace("T", " "),
            "_id": e["_id"]
        } for e in eventos]).sort_values("Fecha")

        mostrar_ids = st.checkbox("Mostrar IDs técnicos (MongoDB)", value=False)
        if not mostrar_ids:
            tabla = tabla.drop(columns="_id")

        st.dataframe(tabla, use_container_width=True, hide_index=True)

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

        # ---- Baja lógica 
        st.subheader("🗑️ Dar de baja un evento")
        st.caption("El evento pasa a estado 'cancelado' y sus órdenes pagadas quedan anuladas, "
                   "por lo que los KPIs se actualizan. Los eventos finalizados no se pueden dar de baja.")

        dables = {
            f"{e['nombre']} ({e['recinto']['ciudad']})": e["_id"]
            for e in eventos if e["estado"] == "programado"
        }
        if not dables:
            st.info("No hay eventos programados para dar de baja.")
        else:
            a_baja = st.selectbox("Evento a dar de baja", list(dables.keys()), key="sel_baja")
            id_baja = dables[a_baja]
            confirmar = st.checkbox("Entiendo que las órdenes pagadas de este evento quedarán anuladas",
                                    key=f"chk_baja_{id_baja}")
            if st.button("Dar de baja", disabled=not confirmar):
                datos, error = pedir("DELETE", f"/eventos/{id_baja}")
                if error:
                    st.error(error)
                else:
                    st.toast(f"Evento dado de baja. Órdenes anuladas: {datos['ordenes_anuladas']} ✅")
                    st.rerun()