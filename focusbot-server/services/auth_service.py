from services.db_service import db, User
from utils import *
from werkzeug.security import generate_password_hash

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

        return {'message':'Usuario creado correctamente', 'id':user.user_id}, 201
    except Exception as e:
        db.session.rollback()
        return {'error':'Error registrando el usuario'}, 500