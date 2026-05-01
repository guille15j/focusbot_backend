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

    # Una vez obtenido el bot vamos a ver si tenemos ese bot registrado con un usuario o si esta libre
    # Enc aso de que este lirbe podremos asignarlo enc aso de que no lo esté protegeremos y blindaremos el bot
    if bot:
        if bot.user_id is not None:
            #En caso de que el parametro de user_id de neustro bot no sea none lo que significa que este bot SI tiene dueño
            return {'error': f'Este FocusBot con nombre {bot.custom_name} ya pertenece a otro usuario'}, 403
        
        # En este caso no estará asociado a ningun usuairo y podremos asociarlo al usuario que tenemos logueado
        bot.user_id = user_id
        bot.custom_name = name
    else:
        #EL bot no se ha encontrado en el sistema asique lo crearemos
        generated_key = secrets.token_hex(16) #contraseña única y aleatoria de 32 caracteres (hexadecimal de 16 bytes)
        # Cuando el robot se conecta por primera vez, la API se la entrega. A partir de ese momento, el robot la usará para identificarse ante el Broker MQTT
        
        bot = Bot(
            mac_address=mac,
            user_id=user_id,
            custom_name=name,
            # pass_key=generated_key,
            # access_point_ssid=f"FocusBot_{mac.replace(':', '')[-4:]}", #Red que crea la ESP para que podamos conectarnos a ellos y ajustar la ssiud de nuestra wifi
            status=BotStatus.IDLE
        )
        db.session.add(bot)

    try:
        db.session.commit()
        return {
            'message': 'FocusBot vinculado con éxito',
            'bot': {
                'id': bot.bot_id,
                'name': bot.custom_name,
                # 'pass_key': bot.pass_key,
                # 'ssid': bot.access_point_ssid
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

    bot  = Bot.query.filter(Bot.user_id == current_user.user_id, Bot.bot_id == bot_id).first()

    if not bot:
        return {"message" : "Bot no encontrado en el sistema"}, 404
    try:

        db.session.delete(bot)
        db.session.commit()

        return {"message" : "Bot borrado con exito"}, 200

    except Exception as e:
        db.session.rollback()
        return {"message" : "Error al borrar el Bot del sistema.", "error" : str(e)}, 500