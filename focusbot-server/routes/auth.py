from flask import Blueprint, jsonify
from services import register_user, login_user, reset_password
from schemas.auth_schema import LoginSchema, ResetPasswordSchema
from schemas.user_schema import UserCreate
from schemas.base import validate_schema

auth_bp = Blueprint('auth', __name__) #Nos permite agripar los endpoints en bloques sin que tengan que estar todos en un mismo archivo

@auth_bp.route('/authcheck', methods=['POST'])
def check():
    return jsonify({"message": "Endpoint de autenticación listo"}), 200

@auth_bp.route('/register', methods=['POST'])
@validate_schema(UserCreate)
def register(user_data: UserCreate):
    # .model_dump() convierte el objeto Pydantic en el dict que espera el servicio
    response, status_code = register_user(user_data.model_dump())
    return jsonify(response), status_code

@auth_bp.route('/login', methods=['POST'])
@validate_schema(LoginSchema)
def login(credentials: LoginSchema):
    response, status_code = login_user(credentials.model_dump())
    return jsonify(response), status_code

@auth_bp.route('/change/password', methods=['POST'])
@validate_schema(ResetPasswordSchema)
def resetPswd(data: ResetPasswordSchema):
    response, status_code = reset_password(data.model_dump())
    return jsonify(response), status_code