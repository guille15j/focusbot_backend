from flask import Blueprint, jsonify, request
from utils import *
from services.history_service import calculateRecord
from services.db_service import History

history_bp = Blueprint('history', __name__)

@history_bp.route('/check', methods=['GET'])
def get_history():
    return jsonify({"message": "API de historial lista para recibir peticones"}), 200

@history_bp.route('/calculate', methods=['POST'])
@token_required
def calculate_history(current_user):
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Datos vacios en la petición.'}), 400
    
    response, status = calculateRecord(current_user, data)

    return jsonify(response), status

@history_bp.route('/<int:record_id>',methods= ['GET'])
@token_required
def get_Recor_by_ID(current_user,record_id):
    return jsonify({
        "message": "Endpoint no implementado",
        "status": "En desarrollo - Próximo sprint"
    }), 501

@history_bp.route('/rango',methods=['GET'])
@token_required
def get_records_en_rango(current_user):
    data = request.get_json()

    return jsonify({
        "message": "Endpoint no implementado",
        "status": "En desarrollo - Próximo sprint"
    }), 501