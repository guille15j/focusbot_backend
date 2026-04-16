from services.db_service import db, User, SeverityEnum
from utils import *
from werkzeug.security import generate_password_hash, check_password_hash

def updateUserPatch(user_id, data):
    """
    Actualiza parcialmente un usuario.
    Solo modifica los campos enviados en el body de la peticion.
    """

    user = User.query.filter(User.user_id == user_id).first()

    if not user:
        return {"error": "Usuario no encontrado"}, 404

    validador = {
        # Gracias a las expresiones lambda podemos manejar el tipo 
        # de dato a almacenar y sus constraints
        "first_name": lambda v: to_str(v, 50),
        "last_name": lambda v: to_str(v, 50),
        "nickname": lambda v: to_str(v, 20),
        "email": lambda v: to_str(v, 100).lower(),
        "phone": lambda v: to_str(v, 20),
        "profile_img": lambda v: v,
        "timezone": lambda v: to_str(v, 50)
    }


    # Lo primero que debemos hacer es comprobar que los campos 
    # nickname y email si estan en el body no se encuentren en usio

    if "email" in data:
        #Usamos el validor para veririficar que tenga el formato correcto
        new_email = validador["email"](data["email"])

        # Comprobamos que no este registrado
        if User.query.filter(User.email == new_email, User.user_id != user_id).first():
            return {"error": "Correo ya registrado por otro usuario"}, 400

    if "nickname" in data:
        #Usamos el validor para veririficar que tenga el formato correcto
        new_nickname = validador["nickname"](data["nickname"])

        # Comprobamos que no este registrado
        if User.query.filter(User.nickname == new_nickname, User.user_id != user_id).first():
            return {"error": "Nickname ya registrado por otro usuario"}, 400

    # Pasamos a comprobar y validar el resto de los componentes de la
    # peticion para actualizar todos los que sean posibels
    try:
        for field, transform in validador.items():
            # Recorremos el validador para verificar item por item
            if field in data:
                # Si el campo del validador esta dentro de los datos del body verificamos
                verificado = transform(data[field])

                # Asignamos el usuario obtenido con el di el atributo neuvo para el campo concreto
                setattr(user, field, verificado)
            
        db.session.commit()

        return {
            "message" : 'Usuario actualizado correctamente.'
        }, 200

    except Exception as e:
        db.session.rollback()
        return {"error": "Error actualizando el usuario"}, 500

def getUser(current_user):
    user = User.query.filter(User.user_id == current_user.user_id).first()

    if not user: 
        return {'error':'Usuario no encontrado.'}, 404

    return {
        'user': {
            'user_id': user.user_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'nickname': user.nickname,
            'email': user.email,
            'phone': user.phone,
            'timezone': user.timezone,
            'profile_img': user.profile_img,
            'name_detail' : user.name_detail,
            'description_detail' : user.description_detail,
            'severity' : user.severity.value if user.severity else None
        }
    }, 200

def getDetail(current_user):
    detail = User.query.filter(User.user_id == current_user.user_id).first()

    if not detail:
        return {'detail':{}}, 200
    
    output = {
        'name_detail': detail.name_detail,
        'description_detail': detail.description_detail,
        'severity': detail.severity.value if detail.severity else None
    }

    return {'detail': output}, 200

def updateDetail(current_user, data):

    detail = User.query.filter(User.user_id == current_user.user_id).first()
    
    validador = {
        "name_detail": lambda v: to_str(v, 50),
        "description_detail": lambda v: to_str(v, 250),
        "severity": lambda v: to_enum(v, SeverityEnum, default=SeverityEnum.LEVE)
    }

    try:
        for f,transform in validador.items():
            if f in data:
                verificado = transform(data[f])
                setattr(detail,f, verificado)

        db.session.commit()

        return {'message' : 'Detalle actualizado con exito.'}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error actualizando el detalle - {e}"}, 500

def createDetail(current_user, data):

    detail = User.query.filter(User.user_id == current_user.user_id).first()

    if not "name_detail" in data:
        return {'error': 'Faltan datos obligatorios'}, 400
    
    try:
        name_d = to_str(data.get('name_detail'),50)
        severidad =  to_enum(data.get('severity'), SeverityEnum, default=SeverityEnum.LEVE)
        descrip = to_str(data.get('description_detail'),250)
        
        detail.name_detail = name_d
        detail.description_detail = descrip
        detail.severity = severidad

        db.session.commit()

        return {
            'message' : 'Detalle registrado correctamente',
        }, 200
    
    except Exception as e:
        db.session.rollback()
        return {'message':'Error durante la creacion del Detalle','error':to_str(e,100)}, 500

