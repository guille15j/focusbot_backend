import paho.mqtt.client as mqtt
import os

# Usamos el nombre que Mosquitto reconoce
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, 
                          client_id="focus_api_server_principal")

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("🟢 API conectada al Broker MQTT")
    else:
        print(f"🔴 Error de conexión. Código: {rc}")

def init_mqtt(app):
    mqtt_client.on_connect = on_connect
    try:
        # "mqtt" es el nombre del servicio docker-compose.yml
        mqtt_client.connect("mqtt", 1883, 60)
        mqtt_client.loop_start() 
        print("Bucle de escucha MQTT iniciado")
    except Exception as e:
        print(f"🔴 No se pudo conectar el cable invisible: {e}")

def asegurar_conexion():
    """Función para que el endpoint verifique si el cable sigue puesto"""
    if not mqtt_client.is_connected():
        try:
            mqtt_client.reconnect()
            return True
        except:
            return False
    return True