from services.db_service import db, User, Activity
from utils import *
from werkzeug.security import generate_password_hash, check_password_hash

def getActivitiesUsr (current_user):

    activities = Activity.query.filter(Activity.user_id == current_user.user_id).all()

    if not activities:
        return {'activities':[]}, 200
    
    lista_act = []
    for a in activities:
        lista_act.append(
            {
                "activity_id": a.activity_id,
                "type_id": a.type_id,
                "user_id": a.user_id,
                "bot_id": a.bot_id,

                "title": a.title,
                "description": a.description,

                "duration_minutes": a.duration_minutes,

                "init_date": a.init_date.isoformat() if a.init_date else None,
                "end_date": a.end_date.isoformat() if a.end_date else None,

                "state": a.state.value, #Envia el valor unico del ENUM
                "category": a.category.value,
                "result": a.result.value if a.result else None
            }
        )
    return {'activities' : lista_act} , 200