from flask import Blueprint, jsonify
from utils import *

activities_bp = Blueprint('activities', __name__)

@activities_bp.route('/check', methods=['GET'])
def get_activities():
    return jsonify({"message": "API preparada para recibir peticiones"}), 200

@activities_bp.route('/user/focus-settings', methods=['GET'])
@token_required
def focusSettings(current_user):
    return None

@activities_bp.route('/user/focus-settings',methods=['POST'])
@token_required
def setFocusSettings(current_user):
    return None

@activities_bp.route('/user/focus-settings', methods=['PATCH'])
@token_required
def updateFocusSettings(current_user):
    return None

# ---------------------------------------------------------------------

@activities_bp.route('/', methods=['GET'])
@token_required
def getActivities(current_user):
    return None

@activities_bp.route('/', methods = ['POST'])
@token_required
def createActivity(current_user):
    return None

@activities_bp.route('/<int:activity_id>', methods= ['PUT'])
@token_required
def updateActivity(current_user):
    return None

@activities_bp.route('/<int:activity_id>', methods= ['DELETE'])
@token_required
def deleteActivity(current_user):
    return None
