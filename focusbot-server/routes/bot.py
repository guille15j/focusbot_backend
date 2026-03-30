from flask import Blueprint, jsonify, request
from services import *
from utils import *

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
@bot_bp.route('/my-robot', methods=['GET'])
@token_required
def get_my_robot(current_user):
    from services.db_service import Bot
    bot = Bot.query.filter_by(user_id=current_user.user_id).first()
    
    if not bot:
        return jsonify({"msg": "No tienes ningún robot vinculado"}), 404
        
    return jsonify({
        "name": bot.custom_name,
        "mac": bot.mac_address,
        "status": bot.status.value,
        "ssid": bot.access_point_ssid
    }), 200

# Testeo de MQTT
@bot_bp.route('/command', methods=['POST'])
def send_command():
    
    from app import mqtt    

    data = request.get_json()
    mac = data.get('mac')
    comando = data.get('comando') # Ejemplo: "FOCUS_ON" o "FOCUS_OFF"

    if not mac or not comando:
        return jsonify({"error": "Falta MAC o comando"}), 400

    topic = f"focusapp/{mac}/command"
    mqtt.publish(topic, comando)
    
    return jsonify({"status": "Enviado", "topic": topic, "msg": comando}), 200