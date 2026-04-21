from pydantic import BaseModel, ConfigDict
from functools import wraps
from flask import request, jsonify
from pydantic import ValidationError

class BaseSchema(BaseModel):
    # Permite a Pydantic leer datos directamente de objetos de SQLAlchemy
    # y convierte automáticamente los Enums a su valor (string/int)
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

def validate_schema(schema_class):
    """Decorador para validar peticiones en las rutas"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json()
                if data is None:
                    return jsonify({"error": "No se recibió un cuerpo JSON válido"}), 400
                
                validated_data = schema_class(**data)
                return f(validated_data, *args, **kwargs)
            except ValidationError as e:
                return jsonify({"error": "Validación fallida", "details": e.errors()}), 422
        return wrapper
    return decorator