from flask import Blueprint, jsonify, request
from services import *
from utils import *

user_bp = Blueprint('users', __name__)

@user_bp.route("/update",methods=['PATCH'])
@token_required
def userUpdate(current_user):
    data = request.get_json()

    if not data:
        return jsonify({"error":"No se han enviado campos para actualizar"}), 400

    response, status_code = updateUserPatch(current_user.user_id, data)

    return jsonify(response), status_code

@user_bp.route("/user",methods=['GET'])
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

    if not data:
        return jsonify({"message":"No se han enviado campos en la petición."}), 400
    
    if request.method == 'POST':
        response, status = createDetail(current_user, data)

    elif request.method in ('PUT','PATCH'):
        response, status = updateDetail(current_user, data)
    else:
        return jsonify({"message": "Método HTTP no permitido"}), 405

    return jsonify(response), status