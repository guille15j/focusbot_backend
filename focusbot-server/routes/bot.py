from flask import Blueprint, jsonify, request
from services import link_bot, getBotsByUser, editBot, getBotById, deleteBot
from services.mqtt_service import mqtt_client, asegurar_conexion
from utils import token_required
from schemas.bot_schema import BotCreate, BotUpdate, BotCommandSchema
from schemas.base import validate_schema

bot_bp = Blueprint('bot', __name__)

@bot_bp.route('/check', methods=['GET'])
def bot_check():
    return jsonify({"msg": "Api bot lista"}), 200

@bot_bp.route('/pair', methods=['POST'])
@token_required
@validate_schema(BotCreate)
def bot_pair(bot_data: BotCreate, current_user):
    response, status_code = link_bot(bot_data.model_dump(), current_user.user_id)
    return jsonify(response), status_code

@bot_bp.route('/getByUser', methods=['GET'])
@token_required
def listadoBots(current_user):
    response, status_code = getBotsByUser(current_user)
    return jsonify(response), status_code

@bot_bp.route('/<int:bot_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
@token_required
def get_edit_delete_bot(current_user, bot_id):
    if request.method == 'DELETE':
        response, status_code = deleteBot(current_user, bot_id)
    elif request.method in ['PUT', 'PATCH']:
        # Validación manual dentro de la ruta multi-método
        data = request.get_json()
        validated = BotUpdate(**data)
        response, status_code = editBot(current_user, bot_id, validated.model_dump(exclude_unset=True))
    else: # GET
        response, status_code = getBotById(current_user, bot_id)
    return jsonify(response), status_code

@bot_bp.route('/command', methods=['POST'])
@validate_schema(BotCommandSchema)
def send_command(cmd_data: BotCommandSchema):
    if not asegurar_conexion():
        return jsonify({"error": "No se pudo reconectar con el Broker"}), 503
    topic = f"focusapp/{cmd_data.mac}/command"
    mqtt_client.publish(topic, cmd_data.comando, qos=0)
    return jsonify({"message": f"Comando enviado a {cmd_data.mac}"}), 200