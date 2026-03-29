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