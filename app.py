import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
from datetime import datetime

# Configuración de la página de Streamlit
st.set_page_config(page_title="SecureBox IoT - Dashboard", layout="wide")

# ============================================================
# CONFIGURACIÓN MQTT Y ESTRUCTURA DE MEMORIA GLOBAL DE RESPALDO
# ============================================================
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_RAIZ = "securebox/unmsm/grupo01/box01/#"
MQTT_ROOT = "securebox/unmsm/grupo01/box01"

# Límite de puntos a mostrar en el gráfico para no saturar la memoria
MAX_PUNTOS_GRAFICO = 30

# Estructura segura fuera del ciclo de vida de Streamlit
if not hasattr(st, "_cache_datos_mqtt"):
    st._cache_datos_mqtt = {
        "door_state": "Desconocido",
        "c1_state": "Desconocido",
        "c1_dist": 0.0,
        "c2_state": "Desconocido",
        "c2_dist": 0.0,
        "alarm_state": "INACTIVE",
        "historial": [],
        # Listas para almacenar las series temporales de los gráficos
        "timeline_grafico": [],
    }


# ============================================================
# FUNCIONES DE CALLBACK MQTT (Corren en segundo plano)
# ============================================================
def on_connect(client, userdata, flags, rc):
    client.subscribe(TOPIC_RAIZ)


def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    topic = msg.topic
    ahora = datetime.now().strftime("%H:%M:%S")

    # 1. Almacenar directamente en la caché del proceso seguro para hilos
    hubo_cambio_distancia = False

    if "door/state" in topic:
        st._cache_datos_mqtt["door_state"] = (
            "ABIERTA" if payload == "open" else "CERRADA"
        )
    elif "compartment/1/state" in topic:
        st._cache_datos_mqtt["c1_state"] = (
            "OCUPADO" if payload == "occupied" else "VACÍO"
        )
    elif "compartment/1/distance" in topic:
        st._cache_datos_mqtt["c1_dist"] = float(payload)
        hubo_cambio_distancia = True
    elif "compartment/2/state" in topic:
        st._cache_datos_mqtt["c2_state"] = (
            "OCUPADO" if payload == "occupied" else "VACÍO"
        )
    elif "compartment/2/distance" in topic:
        st._cache_datos_mqtt["c2_dist"] = float(payload)
        hubo_cambio_distancia = True
    elif "alarm/state" in topic:
        st._cache_datos_mqtt["alarm_state"] = (
            "ACTIVA 🚨" if payload == "active" else "INACTIVA"
        )

    # Inyectar datos al gráfico si llegó una nueva telemetría de distancia
    if hubo_cambio_distancia:
        nuevo_punto = {
            "Hora": ahora,
            "Compartimiento 1 (cm)": st._cache_datos_mqtt["c1_dist"],
            "Compartimiento 2 (cm)": st._cache_datos_mqtt["c2_dist"],
        }
        st._cache_datos_mqtt["timeline_grafico"].append(nuevo_punto)

        # Mantener un tamaño controlado de la lista del gráfico
        if len(st._cache_datos_mqtt["timeline_grafico"]) > MAX_PUNTOS_GRAFICO:
            st._cache_datos_mqtt["timeline_grafico"].pop(0)

    # 2. Procesar Eventos JSON
    if "event" in topic:
        try:
            data = json.loads(payload)
            evento_tipo = data.get("eventType", "EVENTO")
            desc = "Notificación general del sistema"

            if "ACCESS" in evento_tipo:
                desc = f"🔑 {evento_tipo}: Tarjeta [{data.get('uid')}] | Alarma: {data.get('alarmState')}"
            elif "COMPARTMENT" in evento_tipo:
                desc = f"📦 C{data.get('compartment')}: Estado {data.get('state')} ({data.get('distanceCm')} cm)"
            elif "ALARM" in evento_tipo:
                desc = f"🚨 ALARMA: Estado {data.get('state')} | Motivo: {data.get('reason')}"
            elif "SYSTEM" in evento_tipo:
                desc = f"⚙️ Estado del Sistema: {data.get('state')}"

            st._cache_datos_mqtt["historial"].insert(
                0,
                {
                    "Hora": ahora,
                    "Tópico": topic.replace(MQTT_ROOT + "/", ""),
                    "Detalle del Evento": desc,
                },
            )
        except Exception:
            st._cache_datos_mqtt["historial"].insert(
                0,
                {
                    "Hora": ahora,
                    "Tópico": topic.split("/")[-2].upper(),
                    "Detalle del Evento": f"📢 Cambio: {payload}",
                },
            )

    # Forzar refresco visual si Streamlit ya está listo
    try:
        st.rerun()
    except Exception:
        pass


# INICIAR CLIENTE MQTT
@st.cache_resource
def iniciar_mqtt():
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    except AttributeError:
        client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    return client


mqtt_client = iniciar_mqtt()

# ============================================================
# VINCULACIÓN AL SESSION STATE DE STREAMLIT (Hilo Principal)
# ============================================================
st.session_state.door_state = st._cache_datos_mqtt["door_state"]
st.session_state.alarm_state = st._cache_datos_mqtt["alarm_state"]
st.session_state.c1_state = st._cache_datos_mqtt["c1_state"]
st.session_state.c1_dist = st._cache_datos_mqtt["c1_dist"]
st.session_state.c2_state = st._cache_datos_mqtt["c2_state"]
st.session_state.c2_dist = st._cache_datos_mqtt["c2_dist"]
st.session_state.historial = st._cache_datos_mqtt["historial"]
st.session_state.timeline_grafico = st._cache_datos_mqtt["timeline_grafico"]

# ============================================================
# DISEÑO DE LA INTERFAZ GRÁFICA (UI)
# ============================================================
st.title("🔒 SECUREBOX IoT - PANEL DE SUPERVISIÓN")
st.write("Monitoreo en tiempo real de la caja de seguridad inteligente en el borde.")
st.markdown("---")

# Fila 1: Indicadores Principales (Métricas)
col1, col2, col3, col4 = st.columns(4)

with col1:
    color_puerta = "green" if st.session_state.door_state == "CERRADA" else "orange"
    st.markdown(
        f"### Estado Cerrojo\n<h2 style='color:{color_puerta};'>{st.session_state.door_state}</h2>",
        unsafe_allow_html=True,
    )

with col2:
    color_alarma = "red" if "ACTIVA" in st.session_state.alarm_state else "gray"
    st.markdown(
        f"### Alarma General\n<h2 style='color:{color_alarma};'>{st.session_state.alarm_state}</h2>",
        unsafe_allow_html=True,
    )

with col3:
    st.metric(
        label="Compartimiento 1",
        value=st.session_state.c1_state,
        delta=f"{st.session_state.c1_dist} cm",
    )

with col4:
    st.metric(
        label="Compartimiento 2",
        value=st.session_state.c2_state,
        delta=f"{st.session_state.c2_dist} cm",
    )

st.markdown("---")

# Fila 2: SECCIÓN DE GRÁFICOS EN TIEMPO REAL
st.subheader("📈 Analítica de telemetría")

if st.session_state.timeline_grafico:
    # Copiamos los datos para que los cálculos visuales no modifiquen la caché MQTT.
    df_grafico = pd.DataFrame(st.session_state.timeline_grafico)
    columnas_distancia = [
        "Compartimiento 1 (cm)",
        "Compartimiento 2 (cm)",
    ]
    df_grafico[columnas_distancia] = df_grafico[columnas_distancia].apply(
        pd.to_numeric, errors="coerce"
    )
    df_grafico["Muestra"] = range(1, len(df_grafico) + 1)

    # Resumen estadístico de la ventana de telemetría visible.
    resumen = df_grafico[columnas_distancia].agg(["mean", "min", "max"])
    with st.container(horizontal=True):
        st.metric(
            "Promedio C1",
            f"{resumen.loc['mean', columnas_distancia[0]]:.1f} cm",
            border=True,
        )
        st.metric(
            "Promedio C2",
            f"{resumen.loc['mean', columnas_distancia[1]]:.1f} cm",
            border=True,
        )
        st.metric(
            "Distancia mínima",
            f"{resumen.loc['min'].min():.1f} cm",
            border=True,
        )
        st.metric(
            "Distancia máxima",
            f"{resumen.loc['max'].max():.1f} cm",
            border=True,
        )

    grafico_tendencia, grafico_actual = st.columns(2)
    with grafico_tendencia:
        with st.container(border=True):
            st.markdown("**Evolución de las distancias**")
            st.line_chart(
                df_grafico,
                x="Muestra",
                y=columnas_distancia,
                x_label="Muestra recibida",
                y_label="Distancia (cm)",
                height=300,
            )

    with grafico_actual:
        with st.container(border=True):
            st.markdown("**Comparación de la última lectura**")
            lectura_actual = pd.DataFrame(
                {
                    "Compartimiento": ["Compartimiento 1", "Compartimiento 2"],
                    "Distancia (cm)": [
                        st.session_state.c1_dist,
                        st.session_state.c2_dist,
                    ],
                }
            )
            st.bar_chart(
                lectura_actual,
                x="Compartimiento",
                y="Distancia (cm)",
                color="Compartimiento",
                height=300,
            )

    grafico_variacion, grafico_promedio = st.columns(2)
    with grafico_variacion:
        with st.container(border=True):
            st.markdown("**Variación entre lecturas**")
            df_variacion = df_grafico[columnas_distancia].diff().abs()
            df_variacion["Muestra"] = df_grafico["Muestra"]
            st.area_chart(
                df_variacion,
                x="Muestra",
                y=columnas_distancia,
                x_label="Muestra recibida",
                y_label="Cambio absoluto (cm)",
                height=280,
            )

    with grafico_promedio:
        with st.container(border=True):
            st.markdown("**Distancia promedio por compartimiento**")
            promedios = pd.DataFrame(
                {
                    "Compartimiento": ["Compartimiento 1", "Compartimiento 2"],
                    "Promedio (cm)": [
                        resumen.loc["mean", columnas_distancia[0]],
                        resumen.loc["mean", columnas_distancia[1]],
                    ],
                }
            )
            st.bar_chart(
                promedios,
                x="Compartimiento",
                y="Promedio (cm)",
                color="Compartimiento",
                height=280,
            )
else:
    st.info("Esperando telemetría de distancias para generar gráficos dinámicos...")

st.markdown("---")

# Fila 3: Historial Cronológico de Auditoría
st.subheader("📋 Historial Cronológico de Eventos (Auditoría)")

if st.session_state.historial:
    df = pd.DataFrame(st.session_state.historial)

    # El tópico permite agrupar los eventos sin cambiar el formato recibido por MQTT.
    df_eventos = df.copy()
    df_eventos["Tipo de evento"] = (
        df_eventos["Tópico"]
        .str.replace("/event", "", regex=False)
        .str.replace("event/", "", regex=False)
        .str.split("/")
        .str[-1]
        .str.replace("_", " ")
        .str.upper()
    )
    conteo_eventos = (
        df_eventos["Tipo de evento"]
        .value_counts()
        .rename_axis("Tipo de evento")
        .reset_index(name="Cantidad")
    )

    col_eventos, col_tabla = st.columns([1, 2])
    with col_eventos:
        with st.container(border=True):
            st.markdown("**Eventos por categoría**")
            st.bar_chart(
                conteo_eventos,
                x="Tipo de evento",
                y="Cantidad",
                color="Tipo de evento",
                horizontal=True,
                height=320,
            )

    with col_tabla:
        with st.container(border=True):
            st.markdown("**Registro más reciente**")
            st.dataframe(df, hide_index=True, height=320)
else:
    st.info("Esperando eventos desde el simulador Wokwi...")
