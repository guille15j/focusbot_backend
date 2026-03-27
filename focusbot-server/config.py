import os

class Config:
    # Si DATABASE_URL no existe, usa un valor por defecto seguro
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/focusdb")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key")
    MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt")
    MQTT_PORT = 1883