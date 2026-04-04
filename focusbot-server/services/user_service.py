from services.db_service import db, User
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

def getUser(user_id):
    user = User.query.filter(User.user_id == user_id).first()

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
            'profile_img': user.profile_img
        }
    }, 200