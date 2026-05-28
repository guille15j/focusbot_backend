import paho.mqtt.client as mqtt
import os
import json
from services.db_service import db, Bot, Activity, User, ActivityState, ActivityResults, BotStatus
from datetime import datetime, timedelta
import time
# Threading
# El módulo `threading` permite ejecutar código en paralelo (hilos).
# En nuestro caso, el servidor Flask corre en un hilo y el cliente MQTT
# (que está en `loop_start()`) corre en otro. Ambos acceden al mismo
# diccionario `_ultimo_estado`:
#   • Flask escribe al solicitar el estado.
#   • MQTT escribe al recibir la respuesta del bot.
#
# Para evitar que ambos hilos toquen los datos a la vez (condición de
# carrera), usamos un `Lock`.  Solo un hilo puede entrar en el bloque
# `with _estado_lock:` cada vez. El otro espera.
# Asíncrono no significa seguro: si dos hilos comparten memoria, Lock es
# obligatorio.
import threading

# Almacena el último estado recibido por MAC (para verificaciones activas)
_ultimo_estado = {}
_estado_lock = threading.Lock()

# Usamos el nombre que Mosquitto reconoce
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, 
                          client_id="focus_api_server_principal")

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("API conectada al Broker MQTT", flush=True)
    else:
        print(f"Error de conexión. Código: {rc}", flush=True)

def on_message(client, userdata, msg):
    """
    Callback que procesa los mensajes entrantes de los bots.
    Gestiona cambios de estado del bot y resultados de actividades.
    Valida los datos con Pydantic y to_enum antes de delegar en los servicios.
    """
    try:
        with client._flask_app.app_context():
            # Extraer la MAC del topic: focusapp/{mac}/status o focusapp/{mac}/result
            partes = msg.topic.split('/')
            if len(partes) < 3:
                return

            mac = partes[1]  # lo usaremos para filtrar y encontrar el bot real
            tipo = partes[2]  # 'status' o 'result' depende del topic que sea lo usaremos para filtrar y operar

            print(f"[MQTT] Recibido - Topic: {msg.topic}, Payload: {msg.payload.decode()}", flush=True)

            # Para solucionar problemas con importaciones infinitas entre las fucniones que blqouean el fluijno y rompen la fucnion
            from services.db_service import db, Bot, Activity, User
            from services.bot_service import editBot
            from services.activity_service import editActivity
            from utils import to_enum, to_int
            from pydantic import BaseModel, ValidationError

            if tipo == 'status':
                # Validamos con Pydantic con una declaracion interna fde ka clase
                class StatusPayload(BaseModel):
                    status: str

                try:
                    data = json.loads(msg.payload.decode())

                    validated = StatusPayload(**data) #descomponemos el mensaje
                    nuevo_status = validated.status #sacamos el estado

                except (json.JSONDecodeError, ValidationError) as e:
                    print(f"[MQTT] Formato inválido en mensaje de estado de {mac}: {e}", flush=True)
                    return

                if not nuevo_status:
                    print(f"[MQTT] Mensaje de estado incompleto de {mac}", flush=True)
                    return

                # Buscar el bot y el usuario (necesarios tanto para PAUSED como para el resto)
                bot = Bot.query.filter_by(mac_address=mac).first()
                if not bot:
                    print(f"[MQTT] Bot con MAC {mac} no encontrado", flush=True)
                    return

                if bot.user_id is None:
                    print(f"[MQTT] Bot {mac} no tiene usuario vinculado", flush=True)
                    return

                user = User.query.get(bot.user_id)
                if not user:
                    print(f"[MQTT] Usuario {bot.user_id} no encontrado", flush=True)
                    return

                #Tratamiento especial para PAUSED
                if nuevo_status == "PAUSED":
                    print(f"[MQTT] Evento PAUSED recibido de {mac}, pausando actividad...", flush=True)
                    activity = Activity.query.filter_by(
                        bot_id=bot.bot_id,
                        state=ActivityState.EN_CURSO
                    ).first()
                    if activity:
                        editActivity(user, activity.activity_id, {'state': 'PAUSADO'})
                        print(f"[MQTT] Actividad {activity.activity_id} pausada.", flush=True)
                    else:
                        print(f"[MQTT] No se encontró actividad EN_CURSO para el bot {mac}.", flush=True)
                    
                    # El bot sigue en FOCUSING
                    editBot(user, bot.bot_id, {'status': 'FOCUSING'}) #Forzamos por si acaso ha habido algun corte previo
                    bot.last_sync = datetime.utcnow() + timedelta(hours=2)
                    with _estado_lock:
                        _ultimo_estado[mac] = {
                            "status": "PAUSED",
                            "timestamp": datetime.utcnow()
                        }
                    db.session.commit()
                    return

                if nuevo_status == "POSPUESTO":
                    print(f"[MQTT] Evento POSPUESTO recibido de {mac}, devolviendo actividad a pendiente...", flush=True)
                    activity = Activity.query.filter(
                        Activity.bot_id == bot.bot_id,
                        Activity.state.in_([ActivityState.EN_CURSO, ActivityState.PAUSADO])
                    ).first()
                    if activity:
                        activity.state = ActivityState.POSPUESTO
                        print(f"[MQTT] Actividad {activity.activity_id} vuelta a PENDIENTE.", flush=True)
                    else:
                        print(f"[MQTT] No se encontró actividad activa o pausada para el bot {mac}.", flush=True)
                    
                    editBot(user, bot.bot_id, {'status': 'IDLE'})
                    bot.last_sync = datetime.utcnow() + timedelta(hours=2)
                    with _estado_lock:
                        _ultimo_estado[mac] = {
                            "status": "POSPUESTO",
                            "timestamp": datetime.utcnow()
                        }
                    db.session.commit()
                    return

                # Si no es PAUSED, validar que pertenece al enumerador
                status_enum = to_enum(nuevo_status, BotStatus)
                if status_enum is None:
                    print(f"[MQTT] Estado inválido recibido de {mac}: {nuevo_status}", flush=True)
                    return

                if nuevo_status == "FOCUSING":
                    #Si ese apsa a focus comprobacion que no sea que venga de una pausa ( como un bot solo tiene una actividad a la vez y ay tenemos mecansimos que se aseguran de esto buscamos pasuados para es ebot)
                    pausado  = Activity.query.filter(Activity.state == ActivityState.PAUSADO, Activity.bot_id == bot.bot_id).first()

                    if pausado:
                        pausado.state = ActivityState.EN_CURSO
                        db.session.commit()
                        print(f"[MQTT] Actividad {pausado.activity_id} reanudada directamente.", flush=True)

                editBot(user, bot.bot_id, {'status': status_enum.value})
                bot.last_sync = datetime.utcnow() + timedelta(hours=2)
                with _estado_lock:
                    _ultimo_estado[mac] = {
                        "status": nuevo_status,
                        "timestamp": datetime.utcnow()
                    }
                db.session.commit()
                print(f"[MQTT] Estado actualizado: {mac} -> {status_enum.value}", flush=True)

            elif tipo == 'result':
                
                class ResultPayload(BaseModel):
                    activity_id: int
                    result: str

                try:
                    data = json.loads(msg.payload.decode())
                    validated = ResultPayload(**data)
                    activity_id = validated.activity_id
                    resultado = validated.result
                except (json.JSONDecodeError, ValidationError) as e:
                    print(f"[MQTT] Formato inválido en mensaje de resultado de {mac}: {e}", flush=True)
                    return

                if not activity_id or not resultado:
                    print(f"[MQTT] Mensaje de resultado incompleto de {mac}", flush=True)
                    return

                # Validar que el resultado pertenece al enumerador
                result_enum = to_enum(resultado, ActivityResults)
                if result_enum is None:
                    print(f"[MQTT] Resultado inválido recibido de {mac}: {resultado}", flush=True)
                    return

                activity = Activity.query.get(activity_id)
                if not activity:
                    print(f"[MQTT] Actividad {activity_id} no encontrada", flush=True)
                    return

                user = User.query.get(activity.user_id)
                if not user:
                    print(f"[MQTT] Usuario {activity.user_id} no encontrado", flush=True)
                    return

                # Determinar el estado final según el resultado
                if result_enum == ActivityResults.REJECTED:
                    nuevo_estado = ActivityState.CANCELADO
                else:  # SUCCESS o FAILED
                    nuevo_estado = ActivityState.COMPLETADO

                # Actualizar tanto el resultado como el estado
                editActivity(user, activity_id, {
                    'result': result_enum.value,
                    'state': nuevo_estado
                })
                print(f"[MQTT] Resultado y estado actualizados: actividad {activity_id} -> {result_enum.value} ({nuevo_estado.value})", flush=True)

    except Exception as e:
        print(f"[MQTT] Error procesando mensaje: {e}", flush=True)

def init_mqtt(app):
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message  # Registrar callback para mensajes entrantes

    user = os.getenv('MQTT_USER', 'admin')
    password = os.getenv('MQTT_PASSWORD', 'focusbot2026')
    mqtt_client.username_pw_set(user, password)

    try:
        
        host = os.getenv('MQTT_BROKER', 'focus_mqtt')
        mqtt_client.connect(host, 1883, 60)
        mqtt_client._flask_app = app

        # Suscribirse a los topics de estado y resultados de los bots
        mqtt_client.subscribe("focusapp/+/status", qos=1) 
        mqtt_client.subscribe("focusapp/+/result", qos=1) 
        mqtt_client.loop_start() 
        print("Bucle de escucha MQTT iniciado", flush=True)
    except Exception as e:
        print(f" No se pudo conectar el cable invisible: {e}", flush=True)

def asegurar_conexion():
    """Función para que el endpoint verifique si el cable sigue puesto"""
    if not mqtt_client.is_connected():
        try:
            mqtt_client.reconnect()
            return True
        except:
            return False
    return True

def publicar_comando(mac, comando):
    """
    Publica un comando MQTT en el topic del bot correspondiente.
    
    Args:
        mac: dirección MAC del bot de destino.
        payload: diccionario con el contenido del comando a enviar.
    """
    topic = f"focusapp/{mac}/command"
    try:
        mqtt_client.publish(topic, json.dumps(comando), qos=0)
        print(f'[MQTT] Comando publicado: {comando}')
    except Exception as e:
        print(f"[MQTT] Error publicando comando en {topic}: {e}", flush=True)

def verificar_estado_bot(bot_mac):
    """
    Envía SOLICITAR_ESTADO al bot y espera hasta 5 segundos una respuesta
    real en el topic de status. No consulta la base de datos.
    """
    t0 = datetime.utcnow()
    publicar_comando(bot_mac, {"accion": "SOLICITAR_ESTADO"})

    timeout = 5
    interval = 0.5
    waited = 0.0

    while waited < timeout:
        time.sleep(interval)
        waited += interval
        with _estado_lock:
            entry = _ultimo_estado.get(bot_mac)
            if entry and entry["timestamp"] > t0:
                # Estado fresco recibido después de la solicitud
                return entry["status"]

    return None