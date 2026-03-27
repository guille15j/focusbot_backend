from flask import Blueprint, jsonify

activities_bp = Blueprint('activities', __name__)

@activities_bp.route('/', methods=['GET'])
def get_activities():
    return jsonify({"activities": [], "message": "Listado de actividades"}), 200