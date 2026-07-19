# 🔒 SecureBox IoT - Panel de Supervisión

**Monitoreo en tiempo real de una caja de seguridad inteligente en el borde (edge) mediante MQTT y Streamlit.**

---

## 📋 Descripción del Proyecto

SecureBox IoT es un dashboard interactivo desarrollado con **Streamlit** que permite supervisar en tiempo real el estado de una caja de seguridad inteligente. El sistema recibe telemetría y eventos desde dispositivos IoT (simulados con Wokwi) a través del protocolo **MQTT**, procesando la información y presentándola mediante métricas, gráficos dinámicos y un historial de auditoría.

El dashboard muestra:

- Estado del cerrojo (puerta abierta/cerrada)
- Estado de la alarma general
- Estado y distancia de cada compartimento
- Gráficos de evolución de distancias en tiempo real
- Historial cronológico de eventos para auditoría

---

## ✨ Características Principales

- **Monitoreo en tiempo real** de la puerta y compartimentos mediante MQTT.
- **Visualización de métricas** con indicadores de color (verde/naranja/rojo).
- **Gráficos dinámicos**:
  - Evolución temporal de distancias (líneas)
  - Comparación de última lectura (barras)
  - Variación entre lecturas (área)
  - Distancia promedio por compartimento (barras)
- **Resumen estadístico** de la ventana de telemetría visible (promedio, mínimo, máximo).
- **Historial de eventos** con categorización automática (ACCESS, COMPARTMENT, ALARM, SYSTEM).
- **Gráfico de eventos por categoría** para análisis rápido.
- **Actualización automática** de la interfaz al recibir nuevos datos MQTT.

---

## 🏗️ Arquitectura del Sistema

```text
┌─────────────────┐      MQTT       ┌──────────────────────────┐
│  Sensores IoT   │ ──────────────► │   Broker HiveMQ Público  │
│  (Wokwi Sim)    │   (broker.hivemq.com:1883)                  │
└─────────────────┘                 └──────────────────────────┘
                                              │
                                              │ Suscripción a tópicos
                                              ▼
                                    ┌──────────────────────────┐
                                    │   Dashboard Streamlit    │
                                    │   (app.py)               │
                                    │   - Procesamiento MQTT   │
                                    │   - Visualización UI     │
                                    └──────────────────────────┘
```

**Flujo de datos:**

1. Los sensores (simulados en Wokwi) publican mensajes JSON en tópicos MQTT.
2. El broker HiveMQ recibe y distribuye los mensajes.
3. El cliente MQTT en `app.py` se suscribe a los tópicos y procesa los mensajes en segundo plano.
4. Streamlit actualiza la interfaz automáticamente con los nuevos valores.

---

## 🛠️ Tecnologías Utilizadas

- **Python 3.10+**
- **Streamlit** — Framework para el dashboard web interactivo.
- **Paho-MQTT** — Cliente MQTT para la comunicación con el broker.
- **Pandas** — Procesamiento y análisis de datos de telemetría.
- **HiveMQ Broker** — Broker MQTT público para la mensajería.

---

## 📦 Requisitos Previos

- Python 3.10 o superior.
- pip (gestor de paquetes de Python).
- Conexión a Internet (para acceder al broker MQTT público).

---

## 🚀 Instalación y Ejecución

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/trevolcanm10/securebox-iot.git
   cd securebox-iot
   ```

2. **Crear y activar un entorno virtual (opcional pero recomendado):**

   ```bash
   python -m venv env
   # En Windows:
   env\Scripts\activate
   # En Linux/Mac:
   source env/bin/activate
   ```

3. **Instalar dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación:**

   ```bash
   streamlit run app.py
   ```

5. **Abrir el navegador** en la URL que indica Streamlit (generalmente `http://localhost:8501`).

---

## 📡 Tópicos MQTT

El dashboard se suscribe a la raíz `securebox/unmsm/grupo01/box01/#` y procesa los siguientes tópicos:

| Tópico                   | Descripción                   | Payload                                                    |
| ------------------------ | ----------------------------- | ---------------------------------------------------------- |
| `door/state`             | Estado de la puerta           | `open` / `closed`                                          |
| `compartment/1/state`    | Estado del compartimento 1    | `occupied` / `empty`                                       |
| `compartment/1/distance` | Distancia del compartimento 1 | Número (cm)                                                |
| `compartment/2/state`    | Estado del compartimento 2    | `occupied` / `empty`                                       |
| `compartment/2/distance` | Distancia del compartimento 2 | Número (cm)                                                |
| `alarm/state`            | Estado de la alarma general   | `active` / `inactive`                                      |
| `access/event`           | Evento de acceso              | JSON con `eventType`, `uid`, `alarmState`                  |
| `compartment/event`      | Evento de compartimento       | JSON con `eventType`, `compartment`, `state`, `distanceCm` |
| `alarm/event`            | Evento de alarma              | JSON con `eventType`, `state`, `reason`                    |
| `system/event`           | Evento de sistema             | JSON con `eventType`, `state`                              |

---

## 📁 Estructura del Proyecto

```
proyecto_iot/
├── app.py                # Aplicación principal de Streamlit
├── requirements.txt      # Dependencias de Python
├── .gitignore           # Archivos y carpetas ignorados por Git
└── README.md            # Documentación del proyecto
```

---

## 📸 Capturas de Pantalla

_(Próximamente: capturas del dashboard en funcionamiento)_

---

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor:

1. Haz un fork del proyecto.
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y haz commit (`git commit -m 'Agrega nueva funcionalidad'`).
4. Push a la rama (`git push origin feature/nueva-funcionalidad`).
5. Abre un Pull Request.

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo `LICENSE` para más información.

---

## 👨‍💻 Autor

Desarrollado por el equipo de **SecureBox IoT - Grupo 01** para el curso de Internet de las Cosas (UNMSM).
