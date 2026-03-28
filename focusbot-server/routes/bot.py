from flask import Blueprint, jsonify
from services import *
from utils import *

bot_bp = Blueprint('bot', __name__)

@bot_bp.route('/check', methods=['GET'])
def bot_status():
    return jsonify({"msg": "Api bot lista"}), 200

@bot_bp.route('/pair',methods=['POST'])
@token_required
def bot_pair(current_user):
    
    return jsonify({"msg": "Api bot lista"}), 200