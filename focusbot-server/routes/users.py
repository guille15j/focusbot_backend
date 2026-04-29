from flask import Blueprint, jsonify, request
from services import updateUserPatch, getUser, getDetail, createDetail, updateDetail
from utils import token_required
from schemas.user_schema import UserBase # Usamos UserBase para actualizaciones parciales
from schemas.base import validate_schema
from schemas.user_schema import UserBase, UserUpdate

user_bp = Blueprint('users', __name__)

@user_bp.route("/update", methods=['PATCH'])
@token_required
def userUpdate(current_user):
    data = request.get_json()
    # Usamos el schema para validar lo que venga, pero permitimos campos opcionales
    validated = UserUpdate(**data)
    response, status_code = updateUserPatch(current_user.user_id, validated.model_dump(exclude_unset=True))
    return jsonify(response), status_code

@user_bp.route("/user", methods=['GET'])
@token_required
def getUserById(current_user):
    response, status_code = getUser(current_user)
    return jsonify(response), status_code

@user_bp.route("/detail", methods=['GET'])
@token_required
def getUserDetail(current_user):
    response, status_code = getDetail(current_user)
    return jsonify(response), status_code

@user_bp.route("/detail", methods=['PUT', 'PATCH', 'POST'])
@token_required
def manageUserDetail(current_user):
    data = request.get_json()
    if request.method == 'POST':
        response, status = createDetail(current_user, data)
    else: # PUT o PATCH
        response, status = updateDetail(current_user, data)
    return jsonify(response), status