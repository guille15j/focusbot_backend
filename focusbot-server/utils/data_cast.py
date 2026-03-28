from datetime import datetime
import enum

def to_int(value, default=0):
    if value is None: return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def to_float(value, default=0.0):
    if value is None: return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def to_date(date_str, fmt='%Y-%m-%d'):
    if not date_str: return None
    try:
        if isinstance(date_str, datetime):
            return date_str.date()
        return datetime.strptime(date_str, fmt).date()
    except (ValueError, TypeError):
        return None

def to_datetime(dt_str, fmt='%Y-%m-%d %H:%M:%S'):
    if not dt_str: return None
    try:
        if isinstance(dt_str, datetime):
            return dt_str
        return datetime.strptime(dt_str, fmt)
    except (ValueError, TypeError):
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            return None

def to_enum(value, enum_class, default = None):
    """
    Convierte un string al miembro correspondiente de un Enum
    defautl se configurará desde el nombremiento para no tener que crear difenrentes casteos
    """
    if value is None: 
        return default
        
    try:
        if isinstance(value, str):
            return enum_class[value.upper()]

        return enum_class(value)
    except (KeyError, ValueError):

        return default

def to_str(value, limit=None):
    """Limpia y trunca strings"""
    if value is None: return None
    text = str(value).strip()
    if limit:
        return text[:limit]
    return text