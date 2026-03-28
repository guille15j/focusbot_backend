from flask import Flask
from services.db_service import db
from config import Config
from routes import *

def create_app():
    app = Flask(__name__)

    #Configuracion del PostgreSQL
    app.config.from_object(Config)

    #Iniciación de la bd
    db.init_app(app)

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(bot_bp, url_prefix='/bot')
    app.register_blueprint(activities_bp, url_prefix='/activities')
    app.register_blueprint(history_bp, url_prefix='/history')

    # Configuración 
    with app.app_context():
        try:
            db.create_all()
            print("🟢 Conexión exitosa: Tablas sincronizadas en PostgreSQL.")
        except Exception as e:
            print(f"🔴 Error al sincronizar la base de datos: {e}")

    return app

if __name__ == '__main__':
    app = create_app()

    app.run(debug=True,host='0.0.0.0', port=5000)