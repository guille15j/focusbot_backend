from flask import Blueprint, jsonify, request
from services.auth_service import register_user

auth_bp = Blueprint('auth', __name__) #Nos permite agripar los endpoints en bloques sin que tengan que estar todos en un mismo archivo

@auth_bp.route('/authcheck', methods=['POST'])
def check():
    return jsonify({"message": "Endpoint de autenticación listo"}), 200

@auth_bp.route('/register',methods=['POST'])
def register():
    data = request.get_json()

    if not data:
        return jsonify({'error':'Datos vacios en la petición'}),400
    
    response, status_code = register_user(data)

    retrun jsonify(response), status_code