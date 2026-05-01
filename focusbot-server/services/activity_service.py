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
    ).first()

    if not activity:
        return {'error':'Actividad no Registrada en el sistema.'}, 404

    bot = Bot.query.filter(Bot.bot_id == activity.bot_id).first()

    if not bot:
        return {'error' : 'La actividad no tiene un Bot asignado'}, 404

    act_type = ActivityType.query.filter(ActivityType.type_id == activity.type_id).first()

    if not act_type:
        return {'error' : 'La actividad no está asignada a ningun tipo.'} , 404

    act_final = {
        "activity_id": activity.activity_id,
        "title": activity.title,
        "description": activity.description,
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
            # "ssid": bot.access_point_ssid,
            # "version": bot.firmware_version,
            "last_sync": bot.last_sync.isoformat() if bot.last_sync else None
        },

        "type": {
            "type_id": act_type.type_id,
            "name": act_type.name_type,
            "work_duration": act_type.work_duration,
            "short_break": act_type.short_break,
            "long_break": act_type.long_break,
            "cycles_before_long": act_type.cycles_before_long 
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

        init_date = to_datetime(data.get('init_date'))
        end_date = to_datetime(data.get('end_date'))

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
            result = None ,
            metadata = data.get('metadata', {})          
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
    # Transiciones validas entre estados para asegurar las modificaciones
    TRANSICIONES_VALIDAS = {
        ActivityState.PENDIENTE:  [ActivityState.EN_CURSO, ActivityState.POSPUESTO, ActivityState.CANCELADO],
        ActivityState.POSPUESTO:  [ActivityState.EN_CURSO, ActivityState.CANCELADO],
        ActivityState.EN_CURSO:   [ActivityState.COMPLETADO, ActivityState.CANCELADO],
        ActivityState.COMPLETADO: [],   #no hay cambios posibles
        ActivityState.CANCELADO:  [],   #no hay cambiso posibles
    }

    act = Activity.query.filter(
        Activity.activity_id == activity_id,
        Activity.user_id == current_user.user_id
    ).first()

    if not act:
        return {"error": "Actividad no encontrada o no tienes permiso para editarla"}, 404

    estado = data.get('state') # conseguimos el estado al que queremos cambiar
    if estado is not None:
        if estado not in TRANSACCIONES_VALIDAS.get(act.state, []): 
            # conseguimos los posibles estados futuros para el estado actual de la actividad
            # si no se encuentra dentro de las posibilidades lanzaremos errro
            return {
                "message": ( f"Transición de estado no permitida: no se puede pasar de '{act.state.value}' a '{nuevo_state.value}'" )
            }, 400

    #En caso de que el estado sea completado debemos tener si o si un resutlado
    if estado == ActivityState.COMPLETADO and data.get('result') is None:
        return {
            "message": "Para completar una actividad es obligatorio indicar un resultado (SUCCESS o FAILED)."
        }, 400

    #Asignamos automaticamente el resultado de REJECTED cuando toque
    if (act.state == ActivityState.EN_CURSO and nuevo_state == ActivityState.CANCELADO and data.get('result') is None)
        data['result'] = ActivityResults.REJECTED

    try:
        for field, value in data.items():
            if value is not None:
                setattr(act, field, value)

        db.session.commit()
        return {"message": "Actividad actualizada correctamente."}, 200

    except Exception as e:
        db.session.rollback()
        return {"error": "Error actualizando la actividad", "details": str(e)}, 500

def deleteActivity(current_user, activity_id):
    act = Activity.query.filter(Activity.activity_id == activity_id, Activity.user_id == current_user.user_id).first()

    if not act:
        return {'message': 'Actividad no encontrada o no tienes permisos para eliminarla.'}, 404
    
    if act.state in [ActivityState.COMPLETADO, ActivityState.EN_CURSO]:
        return {'message': 'No se pueden eliminar actividades completadas o en curso.'}, 400
    
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
    Se excluyen los tipos marcados como [eliminado] mediante borrado logico
    """
    types = ActivityType.query.filter(
        ActivityType.user_id == current_user.user_id,
        ~ActivityType.name_type.contains('[eliminado]') # no o lo contrario de que el nombre contenga eliminado, es una negacion
    ).all()

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

    # Impedir crear tipos cuyo nombre contenga la marca de eliminado
    if '[eliminado]' in data['name_type']:
        return {'error': 'El nombre del tipo no puede contener la cadena [eliminado]'}, 400

    try:
        new_type = ActivityType(
            user_id = current_user.user_id,
            name_type = data['name_type'],
            work_duration = data['work_duration'],
            short_break = data.get('short_break', 0),
            long_break = data.get('long_break', 0),
            cycles_before_long = data.get('cycles_before_long', 0)
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
    activity_type = ActivityType.query.filter(
        ActivityType.type_id == type_id, 
        ActivityType.user_id == current_user.user_id
    ).first()

    if not activity_type:
        return {"message": "Tipo de actividad no encontrado"}, 404

    # Impedir que se quite/agregue manualmente la marca [eliminado]
    if '[eliminado]' in (activity_type.name_type or ''):
        nuevo_nombre = data.get('name_type')
        if nuevo_nombre is not None and '[eliminado]' not in nuevo_nombre:
            return {
                "message": "No se puede reactivar un tipo de actividad eliminado. Elimine la marca [eliminado] del nombre no está permitido."
            }, 400


    try:
        for field, value in data.items():
            if value is not None:
                setattr(activity_type, field, value)

        db.session.commit()
        return {"message": "Tipo de actividad actualizado correctamente."}, 200

    except Exception as e:
        db.session.rollback()
        return {"message": "Error actualizando el tipo de actividad", "error": str(e)}, 500

def deleteType(current_user, type_id):
    activity_type = ActivityType.query.filter(
        ActivityType.type_id == type_id, 
        ActivityType.user_id == current_user.user_id
    ).first()

    if not activity_type:
        return {"message": "Tipo de actividad no encontrado"}, 404

    system_types = ['Pomodoro', 'Hitos', 'Temporizador']
    if activity_type.name_type in system_types:
        return {"message": "No se pueden eliminar tipos de actividad del sistema"}, 403

    # Verificar que no esté ya marcado como eliminado
    if '[eliminado]' in activity_type.name_type:
        return {"message": "Este tipo de actividad ya ha sido eliminado"}, 400

    try:
        # Borrado logico: se añade la marca al nombre en lugar de borrar el registro
        activity_type.name_type = activity_type.name_type + ' [eliminado]'
        db.session.commit()

        return {
            "message": "Tipo de actividad eliminado correctamente."
        }, 200

    except Exception as e:
        db.session.rollback()
        return {"message": "Error eliminando el tipo de actividad", "error": str(e)}, 500