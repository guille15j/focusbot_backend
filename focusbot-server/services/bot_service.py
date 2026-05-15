from services.db_service import db, Bot, BotStatus, User
import secrets
from utils import *

def getBotsByUser(current_user):
    user = User.query.filter(User.user_id == current_user.user_id).first()

    if not user:
        return {'error':'Usuario no registrado en el sistema.'}, 404

    try:
        bots = Bot.query.filter_by(user_id=current_user.user_id).all()

        if not bots:
            return {"message": "No hay bots registrados para este usuario", "bots": []}, 200

        
        bots_usr =[]
        for bot in bots:
            bots_usr.append(
                {
                "bot_id": bot.bot_id,
                "name": bot.custom_name,
                "mac_address": bot.mac_address,
                "status": bot.status.value,
                # "ssid": bot.access_point_ssid,
                # "version": bot.firmware_version,
                "last_sync": bot.last_sync.isoformat() if bot.last_sync else None
                }
            )

        return {"bots": bots_usr}, 200
    except Exception as e:
        return {'error':f'Error enla carga de bots del usuario - {e}'}, 500

def link_bot(data, user_id):
    mac = data['mac_address']
    name = data['custom_name']

    bot = Bot.query.filter_by(mac_address=mac).first()

    if bot:
        if bot.user_id is not None:
            return {'error': f'Este FocusBot con nombre {bot.custom_name} ya pertenece a otro usuario'}, 403
        
        bot.user_id = user_id
        bot.custom_name = name
    else:
        generated_key = secrets.token_hex(16)
        
        bot = Bot(
            mac_address=mac,
            user_id=user_id,
            custom_name=name,
            status=BotStatus.OFFLINE
        )
        db.session.add(bot)

    try:
        db.session.commit()
        
        # Suscribirse a los topics MQTT del bot recién vinculado
        try:
            from services.mqtt_service import mqtt_client
            mqtt_client.subscribe(f"focusapp/{mac}/status", qos=0)
            mqtt_client.subscribe(f"focusapp/{mac}/result", qos=0)
        except Exception:
            pass

        return {
            'message': 'FocusBot vinculado con éxito',
            'bot': {
                'id': bot.bot_id,
                'name': bot.custom_name,
            }
        }, 201

    except Exception as e:
        db.session.rollback()
        return {'error': f'Error al guardar en la base de datos\n{str(e)}'}, 500
    
def getBotById(current_user, bot_id):
    bot = Bot.query.filter(Bot.bot_id == bot_id, Bot.user_id == current_user.user_id).first()

    if not bot:
        return {"message" : "Bot no encontrado en el sistema"} , 404

    return {   "bot_id": bot.bot_id,
                "name": bot.custom_name,
                "mac_address": bot.mac_address,
                "status": bot.status.value,
                # "ssid": bot.access_point_ssid,
                # "version": bot.firmware_version,
                "last_sync": bot.last_sync.isoformat() if bot.last_sync else None
                }, 201

def editBot(current_user, bot_id, data):
    bot = Bot.query.filter(
        Bot.bot_id == bot_id,
        Bot.user_id == current_user.user_id
    ).first()

    if not bot:
        return {"message": "Bot no encontrado en el sistema"}, 404

    if not data:
        return {"message": "No hay datos que actualizar"}, 200

    try:
        for field, value in data.items():
            if value is not None:
                setattr(bot, field, value)

        db.session.commit()
        return {"message": "Bot actualizado con exito."}, 200

    except Exception as e:
        db.session.rollback()
        return {"message": "Error editando el bot.", "error": str(e)}, 500

def deleteBot(current_user, bot_id):
    bot = Bot.query.filter(Bot.user_id == current_user.user_id, Bot.bot_id == bot_id).first()

    if not bot:
        return {"message": "Bot no encontrado en el sistema"}, 404

    try:
        # Borrado lógico: desvincular el bot del usuario
        bot.user_id = None
        db.session.commit()

        # Desuscribirse de los topics MQTT relacionados con este bot
        try:
            from services.mqtt_service import mqtt_client
            mac = bot.mac_address
            mqtt_client.unsubscribe(f"focusapp/{mac}/status")
            mqtt_client.unsubscribe(f"focusapp/{mac}/result")
        except Exception:
            pass  # Si falla la desuscripción, no afecta al borrado lógico

        return {"message": "Bot desvinculado con éxito"}, 200

    except Exception as e:
        db.session.rollback()
        return {"message": "Error al desvincular el Bot del sistema.", "error": str(e)}, 500