from flask import Flask
from services.db_service import db, User # Importamos db y el modelo User
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost:5432/focusbot_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    try:
        db.create_all()
        print("✅ ¡Tablas creadas correctamente en PostgreSQL!")
        
        if not User.query.first():
            test_user = User(
                first_name="Admin",
                last_name="Focus",
                nickname="admin",
                email="admin@focusbot.com",
                password_hash="hash_seguro_123",
                birth_date="1990-01-01"
            )
            db.session.add(test_user)
            db.session.commit()
            print(" -> Usuario de prueba creado.")
            
    except Exception as e:
        print(f"❌ Error al conectar o crear tablas: {e}")

@app.route('/')
def index():
    return "Servidor FocusBot Online y Base de Datos Conectada."

if __name__ == '__main__':
    app.run(debug=True, port=5000)