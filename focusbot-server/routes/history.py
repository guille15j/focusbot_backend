from flask import Blueprint, jsonify
from utils import *

history_bp = Blueprint('history', __name__)

@history_bp.route('/check', methods=['GET'])
def get_history():
    return jsonify({"message": "API de historial lista para recibir peticones"}), 200

@history_bp.route('/', methods=['GET'])
@token_required
def getHistorial(current_user):
    return None

@history_bp.route('/stats/summary', methods=['GET'])
@token_required
def getSumarioHistorial(current_user):
    return None