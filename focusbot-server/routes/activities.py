from flask import Blueprint, jsonify, request
from services import (getActivitiesUsr, getActivity, createActivity, 
                      editActivity, deleteActivity, getTypesUsr, createType, 
                      editType, deleteType)
from utils import token_required
from schemas.activity_schema import ActivityCreate, ActivityUpdate, ActivityTypeBase
from schemas.base import validate_schema

activities_bp = Blueprint('activities', __name__)

# --- Rutas de Actividades ---
@activities_bp.route('/', methods=['GET'])
@token_required
def getActivities(current_user):
    response, status = getActivitiesUsr(current_user)
    return jsonify(response), status

@activities_bp.route('/<int:activity_id>', methods=['GET'])
@token_required
def getActivityByID(current_user, activity_id):
    response, status = getActivity(current_user, activity_id)
    return jsonify(response), status

@activities_bp.route("/activity", methods=['POST'])
@token_required
@validate_schema(ActivityCreate)
def create_activity_route(act_data: ActivityCreate, current_user):
    response, status = createActivity(current_user, act_data.model_dump())
    return jsonify(response), status

@activities_bp.route("/<int:activity_id>", methods=['PATCH', 'PUT', 'DELETE'])
@token_required
def manage_activity(current_user, activity_id):
    if request.method == 'DELETE':
        response, status = deleteActivity(current_user, activity_id)
    else: # PATCH/PUT
        data = request.get_json()
        validated = ActivityUpdate(**data)
        response, status = editActivity(current_user, activity_id, validated.model_dump(exclude_unset=True))
    return jsonify(response), status

# --- Rutas de Tipos de Actividad ---
@activities_bp.route("/type", methods=['GET', 'POST'])
@token_required
def create_get_type(current_user):
    if request.method == 'GET':
        response, status = getTypesUsr(current_user)
    else: # POST
        data = request.get_json()
        validated = ActivityTypeBase(**data)
        response, status = createType(current_user, validated.model_dump())
    return jsonify(response), status

@activities_bp.route("/type/<int:activity_type_id>", methods=['PUT', 'PATCH', 'DELETE'])
@token_required
def edit_delete_type_route(current_user, activity_type_id):
    if request.method == 'DELETE':
        response, status = deleteType(current_user, activity_type_id)
    else: # PUT/PATCH
        data = request.get_json()
        validated = ActivityTypeBase(**data) # O podrías crear ActivityTypeUpdate
        response, status = editType(current_user, activity_type_id, validated.model_dump(exclude_unset=True))
    return jsonify(response), status