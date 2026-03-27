from flask_sqlalchemy import SQLAlchemy
from datetime import datetim
import enum

db = SQLAlchemy()

# ENUMERADORES
class BotStatus(enum.Enum):
    OFFLINE = "OFFLINE"
    BOOTING = "BOOTING"
    CONFIGURING = "CONFIGURING"
    IDLE = "IDLE"
    FOCUSING = "FOCUSING"
    PAUSED = "PAUSED"
    BREAK = "BREAK"
    FINISHED = "FINISHED"
    ERROR = "ERROR"

class ActivityState(enum.Enum):
    PENDIENTE = 'PENDIENTE'
    POSPUESTO = 'POSPUESTO'
    COMPLETADO = 'COMPLETADO'
    CANCELADO = 'CANCELADO'
    EN_CURSO = 'EN CURSO'

class ActivityCategory (enum.Enum):
    ESTUDIOS = 'ESTUDIOS'
    LECTURA = 'LECTURA'
    HOGAR = 'HOGAR'
    DEPORTES = 'DEPORTES'
    DESCANSO = 'DESCANSO'
    OTRAS = 'OTRAS'

class ServerityEnum (enum.Enum):
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
    password_hash = db.Column(db.Text, nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    profile_img = db.Column(db.Text)
    timezone = db.Column(db.String(50), default='UTC')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    activities = db.relationship('Activity', backref='user', lazy=True)
    bots = db.relationship('Bot', backref='owner', lazy=True)
    details = db.relationship('Detail', backref='user', lazy=True)

class ActivityType (db.Model):
    __tablename__ = "activity_types"

    type_id = db.Column(db.Integer, primary_key= True)
    name_type = db.Column(db.String(50), nullable =False)
    total_time = db.Column(db.Integer, nullable = False)
    rest_time = db.Column(db.Integer, default = 0)
    break_time = db.Column(db.Integer, default = 0)
    num_breaks = db.Column(db.Integer, default = 0)

    # Constraints
    __table_args__ = (
        db.CheckConstraint('rest_time < total_time', name='check_rest_less_than_total'),
        db.CheckConstraint('total_time >= 0', name='check_total_positive'),
        db.CheckConstraint('rest_time >= 0', name='check_rest_positive'),
        db.CheckConstraint('break_time >= 0', name='check_break_positive'),
        db.CheckConstraint('num_breaks >= 0', name='check_num_breaks_positive'),
    )

class Bot(db.Model):
    __tablename__ = 'bots'

    bot_id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(17), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    custom_name = db.Column(db.String(50), default='Focus-Bot')
    pass_key = db.Column(db.Text, nullable=False)
    access_point_ssid = db.Column(db.String(150), nullable=False)
    last_sync = db.Column(db.DateTime)
    status = db.Column(db.Enum(BotStatus), nullable=False, default=BotStatus.OFFLINE)
    firmware_version = db.Column(db.String(20))

class Activity(db.Model):
    __tablename__ = 'activities'

    activity_id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('activity_types.type_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    bot_id = db.Column(db.Integer, db.ForeignKey('bots.bot_id'), nullable=False)

    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250))
    
    duration_minutes = db.Column(db.Integer, nullable=False)
    
    init_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    
    state = db.Column(db.Enum(ActivityState), nullable=False, default=ActivityState.PENDIENTE)
    category = db.Column(db.Enum(ActivityCategory), nullable=False, default=ActivityCategory.OTRAS)

    result = db.Column(db.Enum(ActivityResults), nullable=True)

class Detail(db.Model):
    __tablename__ = 'details'

    detail_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    name_detail = db.Column(db.String(50), nullable=False)
    description_detail = db.Column(db.String(250))
    severity = db.Column(db.Enum(SeverityEnum), default=SeverityEnum.LEVE)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'name_detail', name='uq_user_detail_name'),
    )

# class History(db.Model):
#     __tablename__ = 'histories'

#     result_id = db.Column(db.Integer, primary_key = True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable = False)

#     first_date_range = db.Column(db.DateTime, nullable = False)
#     end_date_range = db.Column(db.DateTime, nullable = False)

#     num_completo = db.Column(db.Integer, default=0)
#     num_pospuesto = db.Column(db.Integer, default=0)
#     num_cancelado = db.Column(db.Integer, default=0)
#     num_pendiente = db.Column(db.Integer, default=0)

#     avg_focus = db.Column(db.Float, default=0.0)
#     total_activities = db.Column(db.Integer, default=0)
#     total_used_time = db.Column(db.Interval)

#     __table_args__ = (
#         db.CheckConstraint('avg_focus >= 0.0', name='check_avg_positive'),

#         db.CheckConstraint('num_completo >= 0.0', name='check_num_completo_positive'),
#         db.CheckConstraint('num_pospuesto >= 0.0', name='check_num_pospuesto_positive'),
#         db.CheckConstraint('num_cancelado >= 0.0', name='check_num_cancelado_positive'),
#         db.CheckConstraint('num_pendiente >= 0.0', name='check_num_pendiente_positive'),

#         db.CheckConstraint('end_date_range >= first_date_range', name='check_date_order'),
#     )

