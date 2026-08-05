# ⚙️ Focus Bot — Servidor Backend

> **API REST centralizada para la gestión del ecosistema IoT de productividad Focus Bot. Actúa como puente entre la aplicación móvil y el dispositivo físico.**

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![MQTT](https://img.shields.io/badge/MQTT-660066?style=for-the-badge&logo=eclipse-mosquitto&logoColor=white)](https://mqtt.org/)

---

## 📑 Tabla de Contenidos

- [Visión General](#-visión-general)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Infraestructura de Contenedores](#-infraestructura-de-contenedores)
- [Seguridad y Autenticación](#-seguridad-y-autenticación)
- [API REST](#-api-rest)
- [Comunicación MQTT](#-comunicación-mqtt)
- [Instalación y Despliegue](#-instalación-y-despliegue)
- [Variables de Entorno](#-variables-de-entorno)

---

## 📌 Visión General

**Focus Bot Server** es el núcleo central del sistema. Implementa una API REST con Flask que gestiona usuarios, dispositivos, actividades y sesiones de trabajo. Además, actúa como puente entre la aplicación móvil y el dispositivo físico mediante el protocolo MQTT, publicando comandos y recogiendo resultados en tiempo real.

---

## 🧩 Arquitectura del Sistema

El backend se despliega sobre una infraestructura de contenedores Docker con tres servicios independientes que comparten una red privada:

```mermaid
graph TD
    A[Focus Bot App] -- REST API --> B[Servidor Flask]
    B -- Persistencia --> C[(PostgreSQL)]
    B -- Publica Comandos --> D[Broker MQTT]
    D -- Entrega Comandos --> E[Dispositivo ESP32]
    E -- Publica Estado/Resultado --> D
    D -- Notifica --> B
```

---

## 📁 Estructura del Proyecto

```text
focusbot-server/
├── app/
│   ├── models/             # Modelos SQLAlchemy (User, Activity, Bot, History)
│   ├── routes/             # Blueprints de la API REST
│   │   ├── auth.py         # Registro, login, verificación, Google OAuth
│   │   ├── users.py        # Perfil y detalles de usuario
│   │   ├── bot.py          # Vinculación, consulta y envío de comandos
│   │   ├── activities.py   # CRUD de actividades y tipos de actividad
│   │   └── history.py      # Cálculo y consulta de históricos
│   ├── services/           # Lógica de negocio
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── bot_service.py
│   │   ├── activity_service.py
│   │   ├── history_service.py
│   │   └── mqtt_service.py # Cliente MQTT (publicación/suscripción)
│   └── utils/              # Decoradores y helpers
│       └── token_required.py
├── Dockerfile              # Imagen personalizada del servidor Flask
├── docker-compose.yml      # Orquestación de servicios
├── requirements.txt        # Dependencias Python
└── .env.example            # Plantilla de variables de entorno
```

---

## 🐳 Infraestructura de Contenedores

El ecosistema de servidores se despliega mediante Docker Compose con tres servicios que comparten la red `focus_net`:

| Servicio | Imagen | Puerto | Función |
| :--- | :--- | :--- | :--- |
| `focus_db` | `postgres:15` | — | Base de datos relacional con healthcheck |
| `focus_mqtt` | `eclipse-mosquitto:2` | 1883 | Broker MQTT para comunicación en tiempo real |
| `focus_api` | Personalizada (`./focusbot-server`) | 5000 | API REST con recarga en caliente para desarrollo |

### Healthcheck de Base de Datos

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres -d ${POSTGRES_DB}"]
  interval: 5s
  timeout: 5s
  retries: 5
```

El servicio `focus_api` depende de que la base de datos esté saludable y de que el broker MQTT esté iniciado antes de arrancar.

---

## 🔒 Seguridad y Autenticación

### JSON Web Tokens (JWT)

- Tokens con validez de **24 horas** generados mediante algoritmo **HMAC-SHA256**.
- El payload contiene el identificador del usuario (`sub`), fecha de emisión (`iat`) y expiración (`exp`).
- La clave secreta (`SECRET_KEY`) se inyecta como variable de entorno.

### Decorador `@token_required`

Protege todas las rutas que requieren autenticación. Realiza cuatro comprobaciones secuenciales:

1. Extrae el token de la cabecera `Authorization: Bearer <token>`.
2. Verifica la firma con la clave secreta.
3. Comprueba que no haya expirado.
4. Confirms que el usuario sigue existiendo en la base de datos.

### Registro y Verificación

- **Contraseñas**: Almacenadas exclusivamente como hash con `werkzeug.security.generate_password_hash()`.
- **Verificación de email**: Código numérico de 6 dígitos enviado por SMTP con TLS. La cuenta permanece bloqueada (`verified = False`) hasta la verificación.
- **Rollback transaccional**: Ante fallos durante el envío del correo, se deshacen todas las operaciones para evitar estados inconsistentes.
- **Google OAuth2**: Autenticación mediante ID Token verificado con la librería oficial `google-auth`.

---

## 🌐 API REST

La API se organiza en **blueprints** por funcionalidad. Todos los endpoints (excepto los de autenticación y el envío de comandos al bot) requieren token JWT válido.

| Blueprint | Prefijo | Endpoints principales |
| :--- | :--- | :--- |
| `auth` | `/auth` | `register`, `login`, `verify`, `google`, `resend-verification`, `change/password` |
| `users` | `/users` | `user` (GET), `update` (PATCH), `detail` (GET/POST/PATCH) |
| `bot` | `/bot` | `check`, `pair`, `getByUser`, `command` |
| `activities` | `/activities` | `/` (GET), `activity` (POST), `<id>` (PATCH/DELETE), `type` (GET/POST) |
| `history` | `/history` | `/` (GET), `calculate` (POST), `<id>` (GET) |

### Validación de datos

Todas las peticiones entrantes se validan con **esquemas Pydantic** antes de ser procesadas por la capa de servicios. Los errores de validación devuelven respuestas `400` con mensajes descriptivos.

---

## 📡 Comunicación MQTT

### Tópicos jerarquizados por dispositivo

Cada dispositivo se identifica por su dirección MAC, generando tres canales exclusivos:

| Tópico | Publicador | Suscriptor | Contenido |
| :--- | :--- | :--- | :--- |
| `focusapp/{mac}/command` | Servidor | Bot | Comandos JSON (iniciar, pausar, reanudar, cancelar) |
| `focusapp/{mac}/status` | Bot | Servidor | Estado del dispositivo (`OFFLINE`, `IDLE`, `FOCUSING`) |
| `focusapp/{mac}/result` | Bot | Servidor | Resultado de la actividad (`SUCCESS`, `FAILED`, `REJECTED`) |

### Calidad de Servicio (QoS 0)

Los comandos se publican con **QoS 0** ("como mucho una vez"). Esta decisión responde al perfil de uso: los comandos son instrucciones en tiempo real generadas por el usuario. Si un comando se pierde por un fallo puntual, el usuario puede reenviarlo desde la aplicación. Un comando duplicado con QoS 1 o 2 podría ejecutar una acción no deseada.

### Gestión de conexión

- **`asegurar_conexion()`**: Verifica el estado del cliente MQTT antes de cada publicación.
- Si la conexión se ha perdido, intenta reconexión automática.
- Si la reconexión falla, el endpoint devuelve **error 503** (Servicio no disponible).

---

## 🚀 Instalación y Despliegue

### Requisitos previos

- [Docker](https://www.docker.com/) y Docker Compose instalados.
- Puertos `5000` y `1883` disponibles en el host.

### Pasos

```bash
# 1. Clonar el repositorio
git clone [https://github.com/tu-usuario/focusbot-server.git](https://github.com/tu-usuario/focusbot-server.git)
cd focusbot-server

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con las credenciales reales

# 3. Construir y levantar los servicios
docker-compose up -d

# 4. Verificar que todos los contenedores están saludables
docker-compose ps
```

### Desarrollo sin Docker

```bash
# Requisitos: Python 3.10+, PostgreSQL 15+, Mosquitto 2+
pip install -r requirements.txt
flask run --host=0.0.0.0 --port=5000
```

---

## 🔐 Variables de Entorno

El archivo `.env` debe contener las siguientes variables:

```ini
# Base de datos PostgreSQL
POSTGRES_USER=focus_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=focusbot_db
DATABASE_URL=postgresql://focus_user:secure_password@focus_db:5432/focusbot_db

# Broker MQTT
MQTT_BROKER=focus_mqtt
MQTT_PORT=1883
MQTT_USER=mqtt_user
MQTT_PASSWORD=mqtt_password

# Seguridad JWT y SMTP
SECRET_KEY=your_jwt_secret_key_here
SMTP_USER=no-reply@focusbot.com
SMTP_PASSWORD=your_app_email_password

# Google OAuth2
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
```
