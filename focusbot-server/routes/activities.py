from flask import Blueprint, jsonify, request
from utils import *
from services import *

activities_bp = Blueprint('activities', __name__)

@activities_bp.route('/check', methods=['GET'])
def activities_check():
    return jsonify({"message": "API preparada para recibir peticiones"}), 200

# ---------------------------------------------------------------------

@activities_bp.route('/', methods=['GET'])
@token_required
def getActivities(current_user):
    response, status_code = getActivitiesUsr(current_user)
    
    return jsonify(response), status_code

@activities_bp.route('/<int:activity_id>', methods=['GET'])
@token_required
def getActivityByID(current_user, activity_id):

    response , status_code = getActivity(current_user, activity_id)
    return jsonify(response), status_code

@activities_bp.route("/activity", methods = ['POST'])
@token_required
def create_activity (current_user):
    data  = request.get_json()

    if not data:
        return jsonify({'message':'Datos vacios en la petición.'}),400
    
    response, status = createActivity(current_user, data)

    return jsonify(response), status

@activities_bp.route("/<int:activity_id>", methods =['PATCH','DELETE','PUT'])
@token_required
def manage_activity(current_user,activity_id ):

    data = request.get_json()

    if request.method in ['PUT','PATCH']:
        if not data:
            return jsonify({'message':'Datos vacios en la petición.'}),400
    
        #Actualizacion
        response, status  = editActivity(current_user, activity_id, data)

    elif request.method == 'DELETE':
        response,  status = deleteActivity(current_user, activity_id)
    else:
        return jsonify({"message": "Método HTTP no permitido"}), 405

    return jsonify(response), status

@activities_bp.route("/type", methods = ['GET', 'POST'])
@token_required
def create_get_type(current_user):
    
    if request.method == 'GET':
        response, status = getTypesUsr(current_user)

    elif request.method == 'POST':
        data = request.get_json()

        if not data:
            return jsonify({'message':'Datos vacios en la petición.'}),400

        response, status = createType(current_user, data)
    else:
        return jsonify({"message": "Método HTTP no permitido"}), 405

    return jsonify(response), status

@activities_bp.route("/type/<int:activity_type_id>", methods = ['PUT','PATCH','DELETE'])
@token_required
def edit_delete_type(current_user, activity_type_id):
    if request.method == 'DELETE':
        response, status = deleteType(current_user, activity_type_id)

    elif request.method in ['PUT', 'PATCH']:
        data = request.get_json()

        response, status = editType(current_user, activity_type_id, data)
    else:
        return jsonify({"message": "Método HTTP no permitido"}), 405

    return jsonify(response), status