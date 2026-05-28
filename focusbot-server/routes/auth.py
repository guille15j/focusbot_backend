from flask import Blueprint, jsonify, request
from services import register_user, login_user, reset_password, verify_email, reenviar_verificacion, delete_user
from schemas.auth_schema import LoginSchema, ResetPasswordSchema, VerifyEmailSchema, ResendVerificationSchema
from schemas.user_schema import UserCreate
from schemas.base import validate_schema
from utils import token_required

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

@auth_bp.route('/verify', methods=['POST'])
def verify_email_route():
    """
    Verifica el email del usuario mediante código de 6 dígitos.
    
    Recibe JSON: { "email": "usuario@correo.com", "codigo": "123456" }
    
    Si el código es correcto:
      - Marca la cuenta como verificada.
      - Devuelve token JWT (el usuario ya puede usar la app).
    """
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Se requiere un cuerpo JSON'}), 400

    validated = VerifyEmailSchema(**data)
    response, status_code = verify_email(validated.email, validated.codigo)
    return jsonify(response), status_code

@auth_bp.route('/resend-code', methods=['POST'])
@validate_schema(ResendVerificationSchema)
def resend_verification_route(validated_data: ResendVerificationSchema):
    """
    Reenvía el código de verificación por correo.
    
    Recibe JSON: { "identifier": "email o nickname" }
    """
    response, status_code = reenviar_verificacion(validated_data.identifier)
    return jsonify(response), status_code

@auth_bp.route('/delete-account', methods=['DELETE'])
@token_required
def delete_account(current_user):
    """
    Elimina permanentemente la cuenta del usuario autenticado.
    Requiere token JWT válido en el header Authorization: Bearer <token>.
    
    Responde:
        200: cuenta eliminada exitosamente.
        404: usuario no encontrado (posible inconsistencia).
        500: error interno al eliminar.
    """
    response, status_code = delete_user(current_user)
    return jsonify(response), status_code