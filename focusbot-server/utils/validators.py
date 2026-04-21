from functools import wraps
from flask import request, jsonify
from pydantic import ValidationError

def validate_schema(schema_class):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json()
                if data is None:
                    return jsonify({"error": "Payload JSON requerido"}), 400
                
                # Validamos y creamos el objeto Pydantic
                validated_data = schema_class(**data)
                
                # Pasamos el objeto validado a la función como argumento
                return f(validated_data, *args, **kwargs)
            except ValidationError as e:
                return jsonify({
                    "error": "Validación Pydantic fallida",
                    "details": e.errors()
                }), 422
        return wrapper
    return decorator