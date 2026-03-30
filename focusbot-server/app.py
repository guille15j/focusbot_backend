from flask import Flask
from flask-mqtt import Mqtt
from services.db_service import db
from config import Config
from routes import *

def create_app():
    app = Flask(__name__) # Instancia de Flask

    #Configuracion del PostgreSQL
    app.config.from_object(Config)

    #Iniciación de la bd
    db.init_app(app)

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(bot_bp, url_prefix='/bot')
    app.register_blueprint(activities_bp, url_prefix='/activities')
    app.register_blueprint(history_bp, url_prefix='/history')

    # Configuración 
    with app.app_context(): # Apertura de la conexion de manera temporal con with
        try:
            db.create_all()
            print("🟢 Conexión exitosa: Tablas sincronizadas en PostgreSQL.")
        except Exception as e:
            print(f"🔴 Error al sincronizar la base de datos: {e}")


    # Configuraicón de broker mqtt
    app.config['MQTT_BROKER_URL'] = 'broker.hivemq.com'     # Configuracion direccion servidor (Broker)
    app.config['MQTT_BROKER_PORT'] = 1883                   # Configuracion del puerto 
    app.config['MQTT_KEEPALIVE'] = 5                        # Conexiones
    app.config['MQTT_TLS_ENABLED'] = False                  

    mqtt = Mqtt (app) # Iniciualizacion del cliente para poder enviar y recibir mensajes por MQTT

    return app

if __name__ == '__main__':
    app = create_app()

    app.run(debug=True,host='0.0.0.0', port=5000)