from flask import Blueprint, jsonify
from services.mqtt_service import mqtt_client

bot_bp = Blueprint('bot', __name__)

@bot_bp.route('/status', methods=['GET'])
def bot_status():
    return jsonify({"status": "connected", "bot_id": "focus_01"}), 200