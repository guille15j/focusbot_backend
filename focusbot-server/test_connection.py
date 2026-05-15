from config import Config
from services.db_service import db, User
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    try:
        # Intenta crear todas las tablas
        db.create_all()
        print("✅ Conexión exitosa a Supabase. Tablas creadas.")
        
        # Lista las tablas creadas
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tablas = inspector.get_table_names()
        print(f"📋 Tablas en la BD: {tablas}")
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")