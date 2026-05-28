from services.db_service import db, User, SeverityEnum
from utils import *
from werkzeug.security import generate_password_hash, check_password_hash

def updateUserPatch(user_id, data):
    user = User.query.filter(User.user_id == user_id).first()
    if not user:
        return {"error": "Usuario no encontrado"}, 404

    # Pydantic ya validó los tipos en el route 
    # aquí solo aplicamos los cambios 
    try:
        for field, value in data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        db.session.commit()
        return {"message": 'Usuario actualizado correctamente.'}, 200
    except Exception as e:
        db.session.rollback()
        return {"error": f"Error actualizando el usuario: {str(e)}"}, 500

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
