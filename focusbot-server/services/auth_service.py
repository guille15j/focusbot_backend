from services.db_service import db, User
from utils import *
from werkzeug.security import generate_password_hash, check_password_hash

def register_user(data):
    """
    Recibe como parametro un diccionario de datos
    Estos datos son recopilados por la aplicación
    
    Esta función comprobara la existencia de dicho usuario
    -> En caso de no estar registrado lo creará
    -> En caso de si estarlo no lo registrará de nuevo
    """   
    # Buscamos que data tenga todos los campos no nulos de la base de datos
    required_fields = ['first_name', 'last_name', 'nickname', 'email', 'birth_date', 'password']
    if any(data.get(field) is None for field in required_fields):
        return {'error': 'Faltan datos obligatorios'}, 400

    email = to_str(data['email'],100).lower()
    nickname = to_str(data['nickname'],20)

    # Buscamos en la base de datos usando el moodelado de USer
    if User.query.filter_by(email = email).first():
        return {'error':'Correo ya registrado en el sistema'}, 400

    if User.query.filter_by(nickname = nickname).first():
        return {'error':'Nickname ya registrado en el sistema'}, 400

    try:
        first_name = to_str(data['first_name'],50)
        last_name = to_str(data['last_name'],50)
        birth_date = to_date(data['birth_date'])
        psswd = data['password']

        # Creacion del hash
        hash_pswd = generate_password_hash(psswd)

        user = User(
            first_name = first_name,
            last_name = last_name,
            nickname = nickname,
            email = email,
            birth_date = birth_date,
            password_hash = hash_pswd,
            phone = to_str(data.get('phone'),20),
            profile_img = data.get('profile_img'),
            timezone = to_str(data.get('timezone'),50)
        ) 

    
        db.session.add(user)
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
    
    if not check_password_hash(user.password_hash, psswd):
        # LA comprobacion del has es negativa por loq ue no se puede iniciar sesión
        return {'message': 'Credenciales inválidas'}, 401

    token = generate_token(user.user_id)
    
    return {
        'message': 'Inicio de sesion completado',
        'token':token,
        'user': {
            'user_id': user.user_id,
            'nickname': user.nickname
        }
    }, 200 

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