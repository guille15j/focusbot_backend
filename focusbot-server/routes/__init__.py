from .auth import auth_bp
from .activities import activities_bp
from .bot import bot_bp
from .history import history_bp
from .users import user_bp
from .google_auth import google_bp

__all__ = [
    'auth_bp',
    'activities_bp',
    'bot_bp',
    'history_bp',
    'user_bp',
    'google_bp'
]