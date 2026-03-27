from flask import Flask
from config import Config
from services.db_service import db
from services.mqtt_service import init_mqtt
# Importaciones corregidas
from routes.auth import auth_bp
from routes.activities import activities_bp
from routes.bot import bot_bp
from routes.history import history_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar base de datos
    db.init_app(app)
    
    # Inicializar MQTT
    init_mqtt(app)

    # Registro de Blueprints con sus prefijos
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(activities_bp, url_prefix='/api/activities')
    app.register_blueprint(bot_bp, url_prefix='/api/bot')
    app.register_blueprint(history_bp, url_prefix='/api/history')

    @app.route('/')
    def index():
        return {"project": "FocusBot API", "status": "online"}, 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)