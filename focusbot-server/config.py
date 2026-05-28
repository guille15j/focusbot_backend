import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")
    MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt")
    MQTT_PORT = 1883
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    API_KEY = os.getenv('API_KEY')