import paho.mqtt.client as mqtt
from config import Config

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("✅ Conexión exitosa al Broker MQTT")
    else:
        print(f"❌ Error de conexión MQTT. Código: {rc}")

def init_mqtt(app):
    mqtt_client.on_connect = on_connect
    try:
        # Usamos el nombre del servicio definido en docker-compose: 'mqtt'
        mqtt_client.connect("mqtt", 1883, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"⚠️ No se pudo iniciar MQTT: {e}")