from flask import Blueprint, jsonify

history_bp = Blueprint('history', __name__)

@history_bp.route('/', methods=['GET'])
def get_history():
    return jsonify({"history": [], "message": "Historial de enfoque"}), 200