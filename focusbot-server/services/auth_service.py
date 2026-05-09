from services.db_service import db, User, SeverityEnum
from utils import *
from werkzeug.security import generate_password_hash, check_password_hash
from services.email_service import generar_codigo_verificacion, enviar_correo_verificacion


def register_user(data):

    # Buscamos que data tenga todos los campos no nulos de la base de datos
    required_fields = ['first_name', 'last_name', 'nickname', 'email', 'birth_date', 'password']
    if any(data.get(field) is None for field in required_fields):
        return {'error': 'Faltan datos obligatorios'}, 400

    email = to_str(data['email'],100).lower()
    nickname = to_str(data['nickname'],20)

    # Buscamos en la base de datos usando el moodelado de USer
    if User.query.filter_by(email = email).first():
        return {'message':'Correo ya registrado en el sistema'}, 400

    if User.query.filter_by(nickname = nickname).first():
        return {'message':'Nickname ya registrado en el sistema'}, 400

    try:
        first_name = to_str(data['first_name'],50)
        last_name = to_str(data['last_name'],50)
        birth_date = to_date(data['birth_date'])
        psswd = data['password']

        # Creacion del hash
        hash_pswd = generate_password_hash(psswd)

        user = User(
            first_name=first_name,
            last_name=last_name,
            nickname=nickname,
            email=email,
            birth_date=birth_date,
            password_hash=hash_pswd,
            phone=to_str(data.get('phone'), 20),
            profile_img=data.get('profile_img'),
            timezone=to_str(data.get('timezone'), 50),
            name_detail=to_str(data.get('name_detail'), 50) or f"Perfil de {nickname}",
            description_detail=data.get('description_detail'),
            severity=SeverityEnum.LEVE
        )
    
        db.session.add(user)
        db.session.flush()  # Obtener el user_id sin tener que hacer un commit aún

        codigo = generar_codigo_verificacion()
        user.verification_token = codigo # guardamos el codiog apra despeus comprobarlo

        enviado = enviar_correo_verificacion(email, codigo)

        if not enviado:
            db.session.rollback()
            return {'message': 'Error enviando el correo de verificación. Inténtalo de nuevo.'}, 500


        db.session.commit()

        token = generate_token(user.user_id)

        return {
            'message':'Usuario creado correctamente', 
            'token': token,
            'id':user.user_id
        }, 201

    except Exception as e:
        db.session.rollback()
        return {'message':'Error registrando el usuario', 'error': str(e)}, 500

def login_user(data):
    identifier = data.get('identifier') 
    psswd = data.get('password')

    if not identifier:
        return {'message': 'Faltan credenciales identifier'}, 400
    if not psswd:
        return {'message': 'Faltan credenciales password'}, 400

    #Buscamos el usuario
    user = User.query.filter(
        (User.email == identifier) | (User.nickname == identifier)
    ).first()

    if not user:
        return {'message': 'Usuario no registrado en el sistema'}, 401
    
    # Si password_hash es NULL, el usuario se registró con Google OAuth2.
    # No puede iniciar sesión con contraseña; debe usar el botón de Google.
    if not user.password_hash:
        return {'message': 'Esta cuenta usa inicio de sesión con Google. Usa ese método para entrar.'}, 401

    
    if not check_password_hash(user.password_hash, psswd):
        # LA comprobacion del has es negativa por loq ue no se puede iniciar sesión
        return {'message': 'Credenciales inválidas'}, 401
    
    if not user.verified:
        return {'message': 'Debes verificar tu correo antes de iniciar sesión. Revisa tu bandeja de entrada o solicita un reenvío.'}, 403

    token = generate_token(user.user_id)
    
    return {
        "message": "Login exitoso",
        "token": token,
        "user": {
            "user_id": user.user_id,
            "nickname": user.nickname,
            "first_name": user.first_name, # Añade estos
            "last_name": user.last_name,   # campos para que
            "email": user.email,           # la App los reciba ya
            "birth_date": str(user.birth_date), # formateados
            "profile_img": user.profile_img, # <--- El string Base64 largo
            "timezone": user.timezone or "UTC",
            "name_detail": user.name_detail,
            "description_detail": user.description_detail,
            "severity": user.severity.value if hasattr(user.severity, 'value') else user.severity
        }
    }, 200 

def verify_email(email, codigo):
    """
    Verifica el email del usuario comparando el código de 6 dígitos
    que introdujo en la app con el almacenado en verification_token.

    Flujo:
      1. Busca al usuario por email.
      2. Si no existe, devuelve 404.
      3. Si ya está verificado, informa (200).
      4. Si no hay código pendiente, error 400.
      5. Si el código no coincide, error 400.
      6. Si coincide: marca verified=True, borra el código, devuelve JWT.

    La búsqueda por email + código evita colisiones accidentales entre
    dos usuarios que pudieran tener el mismo código de 6 dígitos.
    """
    user = User.query.filter_by(email=email).first()

    if not user:
        return {'message': 'Usuario no encontrado'}, 404

    if user.verified:
        return {'message': 'Esta cuenta ya está verificada. Puedes iniciar sesión.'}, 200

    if not user.verification_token:
        return {'message': 'No hay un código de verificación pendiente. Solicita uno nuevo.'}, 400

    if user.verification_token != codigo:
        return {'message': 'Código incorrecto. Revisa el correo e inténtalo de nuevo.'}, 400

    try:
        user.verified = True
        user.verification_token = None 
        db.session.commit()

        # El usuario demostró ser dueño del email: entregamos JWT
        token = generate_token(user.user_id)

        return {
            'message': 'Correo verificado correctamente.',
            "token": token,
            "user": {
                "user_id": user.user_id,
                "nickname": user.nickname,
                "first_name": user.first_name, # Añade estos
                "last_name": user.last_name,   # campos para que
                "email": user.email,           # la App los reciba ya
                "birth_date": str(user.birth_date), # formateados
                "profile_img": user.profile_img, # <--- El string Base64 largo
                "timezone": user.timezone or "UTC",
                "name_detail": user.name_detail,
                "description_detail": user.description_detail,
                "severity": user.severity.value if hasattr(user.severity, 'value') else user.severity
            }
        }, 200

    except Exception as e:
        db.session.rollback()
        return {'message': 'Error verificando el correo', 'error': str(e)}, 500

def reenviar_verificacion(identifier):
    """
    Reenvía el código de verificación por correo cuando el usuario
    no recibió el anterior, lo perdió o expiró.

    - identifier puede ser email o nickname.
    - Si el usuario no existe, devuelve 404.
    - Si ya está verificado, informa sin hacer nada.
    - Si no está verificado, genera un código nuevo (invalidando el anterior)
      y lo envía por correo.
    """
   
    user = User.query.filter(
        (User.email == identifier) | (User.nickname == identifier)
    ).first()

    if not user:
        return {'message': 'Usuario no encontrado'}, 404

    if user.verified:
        return {'message': 'Esta cuenta ya está verificada. Puedes iniciar sesión.'}, 200

    try:
        # Generar código nuevo (el anterior queda invalidado automáticamente)
        codigo = generar_codigo_verificacion()
        user.verification_token = codigo # Aquí se invalida el codigo

        # Enviar el nuevo código por correo
        enviado = enviar_correo_verificacion(user.email, codigo)

        if not enviado:
            db.session.rollback()
            return {'message': 'Error enviando el correo. Inténtalo de nuevo.'}, 500

        db.session.commit()

        return {'message': 'Nuevo código enviado. Revisa tu correo.'}, 200

    except Exception as e:
        db.session.rollback()
        return {'message': 'Error reenviando el código', 'error': str(e)}, 500

def reset_password(data):
    identifier = data.get('identifier') 
    psswd = data.get('password') # Si las contraseñas no coinciden la app no mandara la peticion, solo se recibira una de ellas

    if not identifier:
        return {'message': 'Faltan credenciales identifier'}, 400
    if not psswd:
        return {'message': 'Faltan credenciales password'}, 400

    #Buscamos el usuario
    user = User.query.filter(
        (User.email == identifier) | (User.nickname == identifier)
    ).first()

    if not user:
        return {'message': 'Usuario no registrado en el sistema'}, 401
    
    if check_password_hash(user.password_hash, psswd):
        return {'message': 'No puedes usar la misma contraseña.'}, 422 #No cumple los requitisitos

    try:
        user.password_hash = generate_password_hash(psswd)
        db.session.commit()

        return {'message': 'Cambio de contraseña completado'}, 200

    except Exception as e:
        db.session.rollback()
        return {'message': 'Error actualizando la contraseña','error':str(e)}, 500