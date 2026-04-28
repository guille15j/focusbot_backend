from flask import Blueprint, jsonify, request, current_app
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
from services.db_service import db, User
from utils.security import generate_token
from utils.data_cast import to_str

google_bp = Blueprint('google_auth', __name__)


@google_bp.route('/google', methods=['POST'])
def google_login():
    """
    Autentica o registra un usuario usando Google OAuth2.

    Flujo:
      1. Recibe JSON: { "token": "id_token_de_google" }
      2. Verifica el token contra los servidores de Google.
      3. Extrae: google_id (sub), email, nombre, apellido, foto.
      4. Busca al usuario por google_id. Si existe, autentica.
      5. Si no, busca por email:
         - Si existe, vincula google_id y verifica la cuenta.
         - Si no existe, crea un usuario nuevo con verified=True.
      6. Devuelve JWT de nuestra aplicación.
    """
    data = request.get_json()

    if not data:
        return jsonify({'message': 'Se requiere un cuerpo JSON'}), 400

    token = data.get('token')

    if not token:
        return jsonify({'message': 'Token de Google no proporcionado'}), 400

    try:
        # Verificar el token de Google
        # Esto hace una petición a los servidores de Google para validar la firma
        info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            os.getenv('GOOGLE_CLIENT_ID')
        )

        # Extraer datos del payload de Google
        google_id = info['sub']                       # Identificador único e inmutable
        email = info['email'].lower()                 # Email verificado por Google
        nombre = info.get('given_name', '')           # Nombre (puede no venir)
        apellido = info.get('family_name', '')        # Apellido (puede no venir)
        foto = info.get('picture', '')                # URL de la foto de perfil

        # Buscar usuario por google_id
        user = User.query.filter_by(google_id=google_id).first()

        if not user:
            # No encontrado por google_id, buscar por email
            user = User.query.filter_by(email=email).first()

            if user:
                # El usuario ya existe con email/contraseña
                # Vinculamos Google ID y verificamos automáticamente
                user.google_id = google_id
                user.verified = True
                db.session.commit()
            else:
                # El usuario no existe: crear cuenta nueva
                # Generar nickname único a partir del email
                base_nickname = email.split('@')[0][:20]
                nickname = base_nickname
                contador = 1
                while User.query.filter_by(nickname=nickname).first():
                    nickname = f"{base_nickname}_{contador}"
                    contador += 1

                user = User(
                    first_name=to_str(nombre, 50),
                    last_name=to_str(apellido, 50),
                    nickname=nickname,
                    email=email,
                    password_hash=None,        # Usuario de Google sin contraseña local
                    birth_date=None,           # Google no da fecha de nacimiento
                    profile_img=foto,
                    timezone='UTC',
                    name_detail=f"Perfil de {nickname}",
                    verified=True,             # Google ya verificó el email
                    google_id=google_id
                )

                db.session.add(user)
                db.session.commit()

        # Generar JWT de nuestra aplicación
        jwt_token = generate_token(user.user_id)

        return jsonify({
            'message': 'Inicio de sesión con Google completado',
            'token': jwt_token,
            'user': {
                'user_id': user.user_id,
                'nickname': user.nickname,
                'email': user.email,
                'profile_img': user.profile_img
            }
        }), 200

    except ValueError as e:
        # Token inválido, expirado o manipulado
        return jsonify({'message': 'Token de Google inválido', 'error': str(e)}), 401
    except Exception as e:
        return jsonify({'message': 'Error en autenticación con Google', 'error': str(e)}), 500