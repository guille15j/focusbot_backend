from flask import Blueprint, jsonify, request

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    return jsonify({"message": "Endpoint de autenticación listo"}), 200