from flask import Blueprint, jsonify, request
from utils import *
from services import *

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
def get_Record_by_ID(current_user,record_id):

    response, status = recordByID(current_user,record_id)

    return jsonify(response), status

@history_bp.route('/',methods=['GET'])
@token_required
def get_records(current_user):

    records, status = getAllRecods(current_user)

    return jsonify(records), status