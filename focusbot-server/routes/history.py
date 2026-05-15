from flask import Blueprint, jsonify, request
from utils import *
from services import *
from schemas.history_schema import HistoryCalculate 
from schemas.base import validate_schema

history_bp = Blueprint('history', __name__)

@history_bp.route('/check', methods=['GET'])
def history_check():
    return jsonify({"message": "API de historial lista"}), 200

@history_bp.route('/calculate', methods=['POST'])
@token_required
@validate_schema(HistoryCalculate) 
def calculate_history( validated_data, current_user):
    # validated_data ya es un objeto con init_date_range y end_date_range
    response, status = calculateRecord(current_user, {
        'init_date_range': validated_data.init_date_range,
        'end_date_range': validated_data.end_date_range
    })
    return jsonify(response), status

@history_bp.route('/<int:record_id>', methods=['GET'])
@token_required
def get_Record_by_ID(current_user, record_id):
    response, status = recordByID(current_user, record_id)
    return jsonify(response), status

@history_bp.route('/', methods=['GET'])
@token_required
def get_records(current_user):
    records, status = getAllRecords(current_user)
    return jsonify(records), status