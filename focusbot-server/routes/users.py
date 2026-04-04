from flask import Blueprint, jsonify, request
from services import *
from utils import *

user_bp = Blueprint('users', __name__)

@user_bp.route("/update/<int:user_id>",methods=['PATCH'])
@token_required
def userUpdate(data, user_id):
    data = request.get_json()

    if not data:
        return jsonify({"error":"No se han enviado campos para actualizar"}), 400

    response, status_code = updateUserPatch(user_id, data)

    return jsonify(response), status_code

@user_bp.route("/<int:user_id>",methods=['GET'])
def getUserById(user_id):
    response, status_code = getUser(user_id)

    return jsonify(response), status_code