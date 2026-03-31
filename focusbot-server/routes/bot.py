from flask import Blueprint, jsonify, request
from services import *
from utils import *
import time
from services.mqtt_service import mqtt_client

bot_bp = Blueprint('bot', __name__)

@bot_bp.route('/check', methods=['GET'])
def bot_status():
    return jsonify({"msg": "Api bot lista"}), 200

@bot_bp.route('/pair',methods=['POST'])
@token_required
def bot_pair(current_user):
    data = request.get_json()
    
    if not data:
        return jsonify({'error':'Datos vacios en la petición de vinculación'}),400
    
    response, status_code = link_bot(data, current_user.user_id)

    return jsonify(response), status_code

@bot_bp.route('/status', methods=['GET'])
@token_required
def getStatusBot(current_user):
    return None

@bot_bp.route('/config', methods=['PATCH'])
@token_required
def updateConfig(current_user):
    return None

@bot_bp.route('/unpair', methods=['DELETE'])
@token_required
def deleteBot(current_user):
    return None

# ENDPOINTS DE PRUEBA -----------------------------------------------------------
@bot_bp.route('/bots', methods=['GET'])
@token_required
def get_my_robots(current_user):
    from services.db_service import Bot
    bots = Bot.query.filter_by(user_id=current_user.user_id).all()
    
    if not bots:
        return jsonify([]), 200

    lista_bots = []
    for bot in bots:
        lista_bots.append(
            {
            "bot_id": bot.bot_id,
            "name": bot.custom_name,
            "mac_address": bot.mac_address,
            "status": bot.status.value,
            "ssid": bot.access_point_ssid,
            "version": bot.firmware_version,
            "last_sync": bot.last_sync.isoformat() if bot.last_sync else None
            }
        )
        
    return jsonify(lista_bots), 200

# Testeo de MQTT
@bot_bp.route('/command', methods=['POST'])
def send_command():
    data = request.get_json()
    mac = data.get('mac')
    comando = data.get('comando')

    if not mac or not comando:
        return jsonify({"error": "Falta MAC o comando"}), 400

    # 1. Verificamos que el cable con el broker esté puesto
    if not asegurar_conexion():
        return jsonify({"error": "No se pudo reconectar con el Broker"}), 503

    topic = f"focusapp/{mac}/command"
    
    try:
        # 2. Publicamos el mensaje (QoS 0 es más rápido para pruebas)
        mqtt_client.publish(topic, comando, qos=0)
        print(f"DEBUG: Enviado {comando} al tópico {topic}")
        
        return jsonify({
            "status": "Enviado",
            "destino": topic,
            "comando": comando
        }), 200
    except Exception as e:
        return jsonify({"status": "Error", "msg": str(e)}), 500