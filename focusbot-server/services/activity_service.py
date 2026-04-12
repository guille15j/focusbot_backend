from services.db_service import db, User, Activity, Bot, ActivityType, ActivityCategory, ActivityState, ActivityResults
from utils import *
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


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

def createActivity(current_user, data):
    required_fields = ['type_id','bot_id','title','category']

    if any(data.get(field) is None for field in required_fields):
        return {'message': 'Faltan datos obligatorios'}, 400
    
    try:
        typeId = data['type_id']
        botId = data['bot_id']
        title = to_str(data['title'],100)
        
        category = to_enum(data['category'], ActivityCategory, default= ActivityCategory.OTRAS)

        init_date = data.get('init_date')
        if init_date and isinstance(init_date, str):
            init_date = datetime.fromisoformat(init_date)
            
            
        end_date = data.get('end_date')
        if end_date and isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)

        act = Activity(
            type_id = typeId,
            user_id = current_user.user_id,
            bot_id = botId,
            title = title,
            description = data.get('description'),
            init_date = init_date,
            end_date = end_date,
            state = ActivityState.PENDIENTE,
            category = category,
            result = None            
        )

        db.session.add(act)
        db.session.commit()

        return {
            'message':'Actividad creada correctamente',
            'id':act.activity_id
        }, 201

    except Exception as e:
        db.session.rollback()
        return {'message':'Error registrando la actividad', 'error' : str(e)}, 500

def editActivity(current_user, activity_id, data):
    act = Activity.query.filter(Activity.activity_id == activity_id, Activity.user_id == current_user.user_id).first()

    if not act:
        return {"error": "Actividad no encontrada o no tienes permiso para editarla"}, 404

    validador = {
        "type_id": lambda v: int(v),
        "bot_id": lambda v: int(v),
        "title": lambda v: to_str(v, 100),
        "description": lambda v: to_str(v, 250),
        "init_date": lambda v: datetime.fromisoformat(v) if isinstance(v, str) else v,
        "end_date": lambda v: datetime.fromisoformat(v) if isinstance(v, str) else v,
        "category": lambda v: to_enum(v,ActivityCategory),
        "state": lambda v: to_enum(v,ActivityState),
        "result": lambda v: to_enum(v, ActivityResults)
    }

    try:
        for field, transform in validador.items():
            if field in data and data[field] is not None:
                verificado = transform(data[field])
                setattr(act, field, verificado)
        
        db.session.commit()

        return {
            "message": "Actividad actualizada correctamente."
        }, 200

    except ValueError as ve:
        db.session.rollback()
        return {"error": str(ve)}, 400
    except Exception as e:
        db.session.rollback()
        return {"error": "Error actualizando la actividad", "details": str(e)}, 500

def deleteActivity(current_user, activity_id):
    act = Activity.query.filter(Activity.activity_id == activity_id, Activity.user_id == current_user.user_id).first()

    if not act:
        return {'message': 'Actividad no encontrada o no tienes permisos para eliminarla.'}, 404
    
    if act.get('result') != None or act.get('state') in [ActivityState.COMPLETADO, ActivityState.EN_CURSO] :
        return {'message': 'La actividad ya ha sido realizada y no se puede borrar.'} , 400
    
    try:
        db.session.delete(act)
        db.session.commit()

        return {'message': 'Actividad eliminada correctamente'}, 200

    except Exception as e:
        db.session.rollback()
        return {
            'message': 'Error eliminando la actividad', 
            'error': str(e)
        }, 500

def getTypesUsr(current_user):
    """
    Obtenemos los Tipos de actividad que tiene registrados ese usuario
    """
    types = ActivityType.query.filter(ActivityType.user_id == current_user.user_id).all()

    if not types:
        return {'types': []}, 200

    lista_types = []
    for t in types:
        lista_types.append({
            "type_id": t.type_id,
            "name_type": t.name_type,
            "work_duration": t.work_duration,
            "short_break": t.short_break,
            "long_break": t.long_break,
            "cycles_before_long": t.cycles_before_long
        })

    return {'types': lista_types}, 200

def createType(current_user, data):
    """
    Creación de un nuevo Tipo de Actividad
    """

    required_fields = ['name_type', 'work_duration']

    if any(data.get(field) is None for field in required_fields):
        return {'error': 'Faltan datos obligatorios'}, 400

    try:
        new_type = ActivityType(
            user_id = current_user.user_id,
            name_type = to_str(data['name_type'], 50),
            work_duration = to_int(data['work_duration']),
            short_break = to_int(data.get('short_break'), 0),
            long_break = to_int(data.get('long_break'), 0),
            cycles_before_long = to_int(data.get('cycles_before_long'), 0)
        )

        db.session.add(new_type)
        db.session.commit()

        return {
            'message': 'Tipo de actividad creado correctamente',
            'id': new_type.type_id
        }, 201

    except Exception as e:
        db.session.rollback()
        return {'message': 'Error creando el tipo de actividad', 'error': str(e)}, 500

def editType(current_user, type_id, data):
    """
    Edición de un nuevo tipo de actividad
    """
    activity_type = ActivityType.query.filter(
        ActivityType.type_id == type_id, 
        ActivityType.user_id == current_user.user_id
    ).first()

    if not activity_type:
        return {"error": "Tipo de actividad no encontrado"}, 404

    validador = {
        "name_type": lambda v: to_str(v, 50),
        "work_duration": lambda v: to_int(v),
        "short_break": lambda v: to_int(v),
        "long_break": lambda v: to_int(v),
        "cycles_before_long": lambda v: to_int(v)
    }

    try:
        for field, transform in validador.items():
            if field in data:
                verificado = transform(data[field])
                setattr(activity_type, field, verificado)
        
        db.session.commit()

        return {
            "message": "Tipo de actividad actualizado correctamente."
        }, 200

    except Exception as e:
        db.session.rollback()
        return {"message": "Error actualizando el tipo de actividad", "error": str(e)}, 500

def deleteType(current_user, type_id):
    """
    Eliminación de un tipo de actividad.
    Si la actividad se trata de una de las por defecto (nombre):
        - Pomodoro
        - Hitos
        - Temporizador
    Se deberá lanzar un error y no se podrá eliminar ya que son del sistema.
    De está manera solo se podrán eliinar las propias creadas por el ususario.
    """
    activity_type = ActivityType.query.filter(
        ActivityType.type_id == type_id, 
        ActivityType.user_id == current_user.user_id
    ).first()

    if not activity_type:
        return {"error": "Tipo de actividad no encontrado"}, 404

    system_types = ['Pomodoro', 'Hitos', 'Temporizador']
    if activity_type.name_type in system_types:
        return {"error": "No se pueden eliminar tipos de actividad del sistema"}, 403

    try:
        db.session.delete(activity_type)
        db.session.commit()

        return {
            "message": "Tipo de actividad eliminado correctamente."
        }, 200

    except Exception as e:
        db.session.rollback()
        return {"error": "Error eliminando el tipo de actividad", "details": str(e)}, 500