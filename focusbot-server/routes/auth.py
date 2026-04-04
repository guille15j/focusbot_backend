from flask import Blueprint, jsonify, request
from services import *
from utils import *

auth_bp = Blueprint('auth', __name__) #Nos permite agripar los endpoints en bloques sin que tengan que estar todos en un mismo archivo

@auth_bp.route('/authcheck', methods=['POST'])
def check():
    return jsonify({"message": "Endpoint de autenticación listo"}), 200

@auth_bp.route('/register',methods=['POST'])
def register():
    """
    Permite registrar un usuario en el sistema
    """
    data = request.get_json()

    if not data:
        return jsonify({'error':'Datos vacios en la petición'}),400
    
    response, status_code = register_user(data)

    return jsonify(response), status_code

@auth_bp.route('/login', methods=['POST'])
def loggin():
    """
    Permite gestionar el acceso con credenciales de un usuario devilviendo un 
    token de acceso gestionado con JWT que la aplicacion usará para todas las peticiones
    que lo requieran
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error':'Datos vacios en la petición'}),400
    
    response, status_code = login_user(data)

    return jsonify(response), status_code
