from flask import Blueprint, jsonify, request
from services import *
from utils import *
import time
from services.mqtt_service import mqtt_client, asegurar_conexion

bot_bp = Blueprint('bot', __name__)

@bot_bp.route('/check', methods=['GET'])
def bot_check():
    return jsonify({"msg": "Api bot lista"}), 200

@bot_bp.route('/pair',methods=['POST'])
@token_required
def bot_pair(current_user):
    data = request.get_json()
    
    if not data:
        return jsonify({'message':'Datos vacios en la petición de vinculación'}),400
    
    response, status_code = link_bot(data, current_user.user_id)

    return jsonify(response), status_code

@bot_bp.route('/getByUser',methods=['GET'])
@token_required
def listadoBots(current_user):

    response, status_code = getBotsByUser(current_user)
    return jsonify(response), status_code

@bot_bp.route('/<int:bot_id>', methods=['GET','PUT', 'PATCH', 'DELETE'])
@token_required
def get_edit_delete_bot(current_user, bot_id):
    if request.method == 'DELETE':
        response, status_code = deleteBot(current_user, bot_id)

    elif request.method in ['PUT', 'PATCH']:
        data = request.get_json()

        if not data:
            return jsonify({'message':'Datos vacios en la petición.'}),400

        response, status_code = editBot (current_user, bot_id, data)

    elif request.method == 'GET':
        response, status_code = getBotById(current_user, bot_id)
    
    else:
        return jsonify({"message": "Método HTTP no permitido"}), 405

    return jsonify(response), status_code

# ENDPOINTS DE PRUEBA -----------------------------------------------------------

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