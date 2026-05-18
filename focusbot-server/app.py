from flask import Flask, request, jsonify
from flask_cors import CORS
from services.db_service import db
from config import Config
from routes import *
from services import * 

def create_app():
    app = Flask(__name__) 
    CORS(app, resources={r"/*": {"origins": "*"}})

    @app.before_request
    def check_api_key():
        # Si quieres excluir alguna ruta pública, hazlo aquí
        # if request.path == '/auth/login':
        #     return None  # Permitir login sin API Key (opcional)

        if request.method == 'OPTIONS': # Permitir todas las peticiones preflight (CORS) sin API Key para web
            return None

        api_key = request.headers.get('X-API-Key')
        expected_key =app.config.get('API_KEY')
        if not api_key or api_key != expected_key:
            return jsonify({'message': 'API Key inválida o ausente'}), 401

    # Configuración del PostgreSQL
    app.config.from_object(Config)

    # Iniciación de la bd
    db.init_app(app)

    # Blueprints (Rutas)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(google_bp, url_prefix='/auth')
    app.register_blueprint(bot_bp, url_prefix='/bot')
    app.register_blueprint(activities_bp, url_prefix='/activities')
    app.register_blueprint(history_bp, url_prefix='/history')
    app.register_blueprint(user_bp, url_prefix='/users')

    #Sincronización de Base de Datos
    with app.app_context():
        try:
            db.create_all()
            print("🟢 Conexión exitosa: Tablas sincronizadas.")
        except Exception as e:
            print(f"🔴 Error de BBDD: {e}")

    # INICIAMOS EL SERVICIO MQTT CENTRALIZADO
    init_mqtt(app) 

    return app

if __name__ == '__main__':
    app = create_app()
    # use_reloader=False evita que Flask arranque dos veces y duplique la conexión
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)