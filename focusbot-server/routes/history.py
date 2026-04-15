from flask import Blueprint, jsonify
from utils import *

history_bp = Blueprint('history', __name__)

@history_bp.route('/check', methods=['GET'])
def get_history():
    return jsonify({"message": "API de historial lista para recibir peticones"}), 200

