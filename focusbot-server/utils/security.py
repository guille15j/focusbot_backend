import jwt
import datetime
from flask import current_app

def generate_token(user_id):
    """
    Creacion de token con duracion determinada con contendio del user_id
    """
    try:

        now = datetime.datetime.now(datetime.timezone.utc)

        payload = {
            # Expedicion en 24 horas desde ahora
            'exp': now + datetime.timedelta(days=1),

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