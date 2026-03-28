from .auth import auth_bp
from .activities import activities_bp
from .bot import bot_bp
from .history import history_bp

__all__ = [
    'auth_bp',
    'activities_bp',
    'bot_bp',
    'history_bp'
]