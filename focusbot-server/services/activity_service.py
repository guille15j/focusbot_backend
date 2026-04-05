from services.db_service import db, User, Activity, Bot, ActivityType
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

def getActivity(current_user, activity_id):
    activity = Activity.query.filter(
        Activity.user_id == current_user.user_id, 
        Activity.activity_id == activity_id
    ).frist()

    if not activity:
        return {'error':'Actividad no Registrada en el sistema.'}, 404

    bot = Bot.query.filter(Bot.bot_id == activity.bot_id).frist()

    if not bot:
        return {'error' : 'La actividad no tiene un Bot asignado'}, 404

    act_type = ActivityType.query.filter(ActivityType.type_id == activity.type_id).frist()

    if not act_type:
        return {'error' : 'La actividad no está asignada a ningun tipo.'} , 404

    act_final = {
        "activity_id": activity.activity_id,
        "title": activity.title,
        "description": activity.description,
        "duration_minutes": activity.duration_minutes,
        "init_date": activity.init_date.isoformat() if activity.init_date else None,
        "end_date": activity.end_date.isoformat() if activity.end_date else None,
        "state": activity.state.value,
        "category": activity.category.value,
        "result": activity.result.value if activity.result else None,

        "bot": {
            "bot_id": bot.bot_id,
            "name": bot.custom_name,
            "mac_address": bot.mac_address,
            "status": bot.status.value,
            "ssid": bot.access_point_ssid,
            "version": bot.firmware_version,
            "last_sync": bot.last_sync.isoformat() if bot.last_sync else None
        },

        "type": {
            "type_id": act_type.type_id,
            "name": act_type.name_type,
            "total_time": act_type.total_time,
            "rest_time": act_type.rest_time,
            "break_time": act_type.break_time,
            "num_breaks": act_type.num_breaks
        }
    }

    return {"activity": act_final}, 200

    