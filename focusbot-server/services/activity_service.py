from services.db_service import db, User, Activity, Bot, ActivityType, ActivityCategory, ActivityState, ActivityResults
from services.mqtt_service import publicar_comando
from utils import *
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from flask import jsonify

def getActivitiesUsr(current_user):
    print('Iniciando recoleccion de actividades')
    
    try:
        # 1. Obtener todas las actividades del usuario
        activities = Activity.query.filter_by(user_id=current_user.user_id).all()
        print(f' - Devolviendo {len(activities)} actividades')
        result = []

        for act in activities:

            # 2. Búsqueda del Tipo asociado
            tipo = ActivityType.query.get(act.type_id)
            
            # 3. Búsqueda del Bot asociado
            bot = Bot.query.get(act.bot_id)

            # 4. Construcción del objeto de respuesta con serialización manual
            act_dict = {
                'activity_id': act.activity_id,
                'title': act.title,
                # Serialización de Enums de la Actividad (.value)
                'state': act.state.value if hasattr(act.state, 'value') else str(act.state),
                'category': act.category.value if hasattr(act.category, 'value') else str(act.category),
                'init_date': act.init_date.isoformat() if act.init_date else None,
                'end_date': act.end_date.isoformat() if act.end_date else None,
                'extra_data': act.extra_data or {},
                
                # Objeto del Tipo (ActivityType)
                'type': {
                    'type_id': tipo.type_id,
                    'name_type': tipo.name_type,
                    'work_duration': tipo.work_duration,
                    'short_break': tipo.short_break,
                    'long_break': tipo.long_break,
                    'cycles_before_long': tipo.cycles_before_long
                } if tipo else None,

                # Objeto del Bot (corrigiendo el error de BotStatus)
                'bot': {
                    'bot_id': bot.bot_id,
                    'name': bot.custom_name,
                    # Aquí es donde fallaba: convertimos el Enum del Bot a String/Value
                    'status': bot.status.value if hasattr(bot.status, 'value') else str(bot.status)
                } if bot else None
            }
            result.append(act_dict)
            print(f' - Iteracion numero {len(result)}')
        
        # Retornamos la lista directamente (el router se encarga del jsonify)
        return result, 200

    except Exception as e:
        # Imprime el error exacto en la consola de Flask para debug
        print(f"❌ ERROR EN getActivitiesUsr: {str(e)}")
        return {
            'message': 'Error al obtener las actividades',
            'error': str(e)
        }, 500

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
            init_date = init_date,
            end_date = end_date,
            state = ActivityState.PENDIENTE,
            category = category,
            result = None ,
            extra_data = data.get('extra_data', {})          
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
        ActivityState.EN_CURSO:   [ActivityState.COMPLETADO, ActivityState.CANCELADO, ActivityState.PAUSADO],
        ActivityState.PAUSADO:    [ActivityState.EN_CURSO, ActivityState.CANCELADO],
        ActivityState.COMPLETADO: [],
        ActivityState.CANCELADO:  [],
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
    estado_previo = act.state
    if (estado_previo in [ActivityState.EN_CURSO, ActivityState.PAUSADO] and 
        estado == ActivityState.CANCELADO and 
        data.get('result') is None):
        data['result'] = ActivityResults.REJECTED

    try:
        for field, value in data.items():
            if value is not None:
                setattr(act, field, value)

        db.session.commit()
        
        #Enviamos el comando una vez que se actuliza el estado (mac + coamndo)
        
        # validamos si se trata de un cambio de estado lo primero
        # si no se trata de un cambio d eestado ni lo trato paso al retrun
        if estado is not None:
            # SI se trata de un cambio de estado valido que sea un cambio a:
            # CANCELADO, EN_CURSO, PAUSADO
            # Si es un cambio a POSPUESTO -> no afecta al bot no hay comando
            # Si es un cambio a COMPLETADO -> se ejecuta en el bot no en la app por el usuario
            # Nunca puede volver a PENDIENTE por lo que no hay comando
            if estado in [ActivityState.EN_CURSO, ActivityState.PAUSADO,  ActivityState.CANCELADO]:
                comando = construirComando(act, estado, estado_previo)
                #enviamos comando al servicio de m1qtt
                if comando:
                    bot = Bot.query.get(act.bot_id)
                    if bot and bot.mac_address:
                        publicar_comando(bot.mac_address, comando)

        return {"message": "Actividad actualizada correctamente."}, 200

    except Exception as e:
        db.session.rollback()
        return {"error": "Error actualizando la actividad", "details": str(e)}, 500

def deleteActivity(current_user, activity_id):
    act = Activity.query.filter(Activity.activity_id == activity_id, Activity.user_id == current_user.user_id).first()

    if not act:
        return {'message': 'Actividad no encontrada o no tienes permisos para eliminarla.'}, 404
    
    if act.state in [ActivityState.COMPLETADO, ActivityState.EN_CURSO, ActivityState.PAUSADO]:
        return {'message': 'No se pueden eliminar actividades completadas, en curso o pausadas.'}, 400
    
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
    Crea un nuevo Tipo de Actividad.
    Si ya existe un tipo con los mismos parámetros para el usuario, reutiliza ese.
    """
    try:
        name = data['name_type']
        work = data['work_duration']
        short = data.get('short_break', 0)
        long_ = data.get('long_break', 0)
        cycles = data.get('cycles_before_long', 0)

        # Buscar si ya existe un tipo idéntico
        existing = ActivityType.query.filter_by(
            user_id=current_user.user_id,
            name_type=name,
            work_duration=work,
            short_break=short,
            long_break=long_,
            cycles_before_long=cycles
        ).first()

        if existing:
            return {
                'message': 'Ya existe un tipo de actividad con estos parámetros',
                'id': existing.type_id
            }, 200

        # Si no existe, crear uno nuevo
        new_type = ActivityType(
            user_id=current_user.user_id,
            name_type=name,
            work_duration=work,
            short_break=short,
            long_break=long_,
            cycles_before_long=cycles
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

def construirComando(activity, estado, estado_previo):
    """
    Construye el payload MQTT correspondiente a la transición de estado.
    La actividad ya tiene los cambios aplicados en el objeto Python.
    """
    comando = {}
    match estado:
        case ActivityState.EN_CURSO:
            if estado_previo == ActivityState.PAUSADO:
                # Reanudar actividad pausada
                comando = {
                    "accion": "REANUDAR_ACTIVIDAD",
                    "activity_id": activity.activity_id
                }
            else:
                # Iniciar actividad desde PENDIENTE o POSPUESTO
                tipo = ActivityType.query.get(activity.type_id)
                parametros = {
                    "work_duration": tipo.work_duration,
                    "short_break": tipo.short_break,
                    "long_break": tipo.long_break,
                    "cycles_before_long": tipo.cycles_before_long
                }
                comando = {
                    "accion": "INICIAR_ACTIVIDAD",
                    "activity_id": activity.activity_id,
                    "tipo": tipo.name_type,
                    "parametros": parametros,
                    "extra_data": activity.extra_data or {}
                }

        case ActivityState.PAUSADO:
            # Pausar la actividad en curso
            comando = {
                "accion": "PAUSAR_ACTIVIDAD",
                "activity_id": activity.activity_id
            }

        case ActivityState.CANCELADO:
            # Cancelar la actividad en curso o pausada
            comando = {
                "accion": "FINALIZAR_ACTIVIDAD",
                "activity_id": activity.activity_id
            }

    return comando
