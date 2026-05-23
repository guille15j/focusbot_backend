import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app
from services import *

def generate_token(user_id):
    """
    Creacion de token con duracion determinada con contendio del user_id
    """
    try:

        now = datetime.datetime.now(datetime.timezone.utc)

        payload = {
            # Expedicion en 24 horas desde ahora
            'exp': now + datetime.timedelta(days=1),
            # 'exp': now + datetime.timedelta(minutes=5),

            # Iniciacion desde el momento actual
            'iat': now,
            'sub': str(user_id) #Sub == subject - sujeto en este caso ID del susuario
        }

        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    except Exception as e:
        return str(e)

def token_required(function):
    """
    Definicion del decorador que actuará sobre las funciones pasadas como
    parámetro, por lo general los endpoints de routes.

     - function: función encargada de manejar el endpoint a proteger.
    """
    @wraps(function) 
    # Sirve para que la función f no olvide su nombre original. Sin esto,
    # si preguntaras el nombre de la ruta, Python diría que se llama 
    # decorated en lugar de su nombre original
    def decorated(*args, **kwargs):
        token = None
        # El estándar es enviar el token en el Header 'Authorization'
        # "Authorization": "Bearer <token>"
        if 'Authorization' in request.headers:
            # Si se detecta el campo Authorization dentro del header So sacamos
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "): # Nos quedamos solo con el token
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'message': 'No se ha encontrado un token en la petición'}), 401

        try:
            # Decodificamos el token usando la SECRET_KEY con el mismo metodo de codificación
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])

            # Buscamos al usuario en la DB para asegurarnos de que sigue existiendo
            current_user = User.query.filter_by(user_id=data['sub']).first()

            if not current_user:
                return jsonify({'message': 'Usuario no válido'}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Tu sesión ha expirado, logueate de nuevo'}), 401

        except Exception as e:
            return jsonify({'message': 'Token inválido o corrupto'}), 401

        # Pasamos el usuario encontrado a la función de la ruta
        return function(current_user, *args, **kwargs)

    return decorated

def require_api_key():
    api_key = request.headers.get('X-API-Key')
    expected_key = os.getenv('API_KEY')
    if not api_key or api_key != expected_key:
        return jsonify({'error': 'API Key inválida o ausente'}), 401
    return None  # continuar con la petición