from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()

# ENUMERADORES
class BotStatus(enum.Enum):
    OFFLINE = "OFFLINE"
    IDLE = "IDLE"
    FOCUSING = "FOCUSING"

class ActivityState(enum.Enum):
    PENDIENTE = 'PENDIENTE'
    POSPUESTO = 'POSPUESTO'
    COMPLETADO = 'COMPLETADO'
    CANCELADO = 'CANCELADO'
    EN_CURSO = 'EN_CURSO' 
    PAUSADO = 'PAUSADO'  

class ActivityCategory (enum.Enum):
    ESTUDIOS = 'ESTUDIOS'
    LECTURA = 'LECTURA'
    HOGAR = 'HOGAR'
    DEPORTES = 'DEPORTES'
    DESCANSO = 'DESCANSO'
    OTRAS = 'OTRAS'

class SeverityEnum (enum.Enum):
    LEVE = 'LEVE'
    MEDIO = 'MEDIO'
    ALTO = 'ALTO'

class ActivityResults(enum.Enum):
    SUCCESS = 'SUCCESS'
    REJECTED = 'REJECTED' 
    FAILED = 'FAILED'

# Definicion de los modelos de tablas

# Para que Flask entienda la clase como tabla debe heredar de dn.Model
class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    nickname = db.Column(db.String(20), nullable=False, unique=True)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100), nullable=False, unique=True)
    
    # Se permite NULL para usuarios autenticados con Google OAuth2,
    # ya que Google gestiona la contraseña y nosotros no debemos almacenarla.
    password_hash = db.Column(db.Text, nullable=True)

    # Se permite NULL para usuarios de Google OAuth2, ya que Google no proporciona
    # la fecha de nacimiento en el scope básico de autenticación.
    # El usuario puede completarla posteriormente desde la sección de perfil.
    birth_date = db.Column(db.Date, nullable=True)
    
    # Indica si el usuario ha verificado su email mediante el enlace enviado tras el registro.
    # Por defecto es False. Se cambia a True cuando el usuario hace clic en el enlace.
    # Los usuarios de Google OAuth2 se crean con verified=True automáticamente,
    # porque Google ya ha verificado el email del usuario.
    verified = db.Column(db.Boolean, default=False, nullable=False)

    # Almacena el token de verificación enviado por email tras el registro.
    # Se genera en el momento del registro y se elimina (se pone a NULL)
    # cuando el usuario verifica su email correctamente.
    # Es nullable=True porque:
    #   - Los usuarios de Google no pasan por este flujo (se crean como verified=True).
    #   - Los usuarios que ya verificaron su email no necesitan conservarlo.
    verification_token = db.Column(db.String(255), nullable=True)

    # Identificador único del usuario en Google (campo 'sub' del token OAuth2).
    # Permite vincular de forma inmutable una cuenta de Google con un usuario de nuestra app.
    #   - Es unique=True porque cada cuenta de Google solo puede estar vinculada a un usuario.
    #   - Es nullable=True porque los usuarios registrados con email/contraseña no tienen Google ID.
    #   - Si un usuario de email/contraseña luego usa Google, se vincula este campo a su cuenta.
    google_id = db.Column(db.String(255), nullable=True, unique=True)

    profile_img = db.Column(db.Text)
    timezone = db.Column(db.String(50), default='UTC')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
 
    name_detail = db.Column(db.String(50))
    description_detail = db.Column(db.String(250))
    severity = db.Column(db.Enum(SeverityEnum), default=SeverityEnum.LEVE)

    activities = db.relationship('Activity', backref='user', lazy=True)
    bots = db.relationship('Bot', backref='owner', lazy=True)

class Activity(db.Model):
    __tablename__ = 'activities'

    activity_id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('activity_types.type_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    bot_id = db.Column(db.Integer, db.ForeignKey('bots.bot_id'), nullable=False)

    title = db.Column(db.String(100), nullable=False)
    
    # duration_minutes = db.Column(db.Integer, nullable=False)
    
    init_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    
    state = db.Column(db.Enum(ActivityState), nullable=False, default=ActivityState.PENDIENTE)
    category = db.Column(db.Enum(ActivityCategory), nullable=False, default=ActivityCategory.OTRAS)

    result = db.Column(db.Enum(ActivityResults), nullable=True)

    extra_data = db.Column(JSON, nullable = True, default = {})

class ActivityType(db.Model):
    __tablename__ = "activity_types"

    type_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    name_type = db.Column(db.String(50), nullable=False)
    work_duration = db.Column(db.Integer, nullable=False)
    short_break = db.Column(db.Integer, default=0)
    long_break = db.Column(db.Integer, default=0)
    cycles_before_long = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.CheckConstraint('work_duration >= 0', name='check_work_duration_positive'),
        db.CheckConstraint('short_break >= 0', name='check_short_break_positive'),
        db.CheckConstraint('long_break >= 0', name='check_long_break_positive'),
        db.CheckConstraint('cycles_before_long >= 0', name='check_cycles_before_long_positive'),
    )

class Bot(db.Model):
    __tablename__ = 'bots'

    bot_id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(17), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    custom_name = db.Column(db.String(50), default='Focus-Bot')

    # pass_key = db.Column(db.Text, nullable=False)
    # access_point_ssid = db.Column(db.String(150), nullable=False)

    last_sync = db.Column(db.DateTime)
    status = db.Column(db.Enum(BotStatus), nullable=False, default=BotStatus.OFFLINE)
   
    # firmware_version = db.Column(db.String(20))

class History(db.Model):
    __tablename__ = 'histories'

    record_id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable = False)

    init_date_range = db.Column(db.DateTime, nullable = False)    # Fecha inicial del rango
    end_date_range = db.Column(db.DateTime, nullable = False)     # Fecha final del rango

    num_completo = db.Column(db.Integer, default=0)               # Num de actividades con resultado completado
    num_pospuesto = db.Column(db.Integer, default=0)              # Num de actividades con estado pospuesto
    num_cancelado = db.Column(db.Integer, default=0)              # Num de actividades con resultado cancelado
    num_pendiente = db.Column(db.Integer, default=0)              # Num de actividades con resultado a null && estado != pospuesto

    most_category = db.Column(db.Enum(ActivityCategory))          # Categoría más repetida en el rango
    total_activities = db.Column(db.Integer, default=0)           # Numero de actividades analizadas
    total_used_time = db.Column(db.Integer)                       # Tiempo total invertido en minutos

    __table_args__ = (
        db.CheckConstraint('num_completo >= 0', name='check_num_completo_positive'),
        db.CheckConstraint('num_pospuesto >= 0', name='check_num_pospuesto_positive'),
        db.CheckConstraint('num_cancelado >= 0', name='check_num_cancelado_positive'),
        db.CheckConstraint('num_pendiente >= 0', name='check_num_pendiente_positive'),
        db.CheckConstraint('total_activities >= 0', name='check_total_activities_positive'),
        db.CheckConstraint('total_used_time >= 0', name='check_total_used_time_positive'),
        db.CheckConstraint('end_date_range >= init_date_range', name='check_date_order'),
    )
