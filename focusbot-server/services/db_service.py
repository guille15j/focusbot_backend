from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Definicion de los modelos de tablas

# Para que Flask entienda la clase como tabla debe heredar de dn.Model
class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column (db.Integer, primary_key = True)
    name_usr = db.Column (db.String(50), nullable=False )
    srname_usr = db.Column (db.String(50), nullable=False  )
    nickname = db.Column (db.String(20), nullable=False  )
    phone = db.Column (db.Integer )
    mail = db.Column (db.String(100), nullable=False  )
    hash_pwsd = db.Column (db.Text, nullable=False  )
    bth_date = db.Column (db.Date, nullable=False  )
    img = db.Column (db.Text )
    timezone = db.Column(db.String(50), default='UTC')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ActivityType (db.Model):
    __tablename__ = "activity_types"

    type_id = db.Column(db.Integer, primary_key= True)
    total_time = db.Column(db.Integer, nullable = False)
    rest_time = db.Column(db.Integer, default = 0)
    break_time = db.Column(db.Integer, default = 0)
    num_breaks = db.Column(db.Integer, default = 0)
    name_type = db.Column(db.String(50), nullable =False)

    # Constraints
    __table_args__ = (
        CheckConstraint('rest_time < total_time', name='check_rest_less_than_total'),
        CheckConstraint('total_time >= 0', name='check_total_positive'),
        CheckConstraint('rest_time >= 0', name='check_rest_positive'),
        CheckConstraint('break_time >= 0', name='check_break_positive'),
        CheckConstraint('num_breaks >= 0', name='check_num_breaks_positive'),
    )

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


class Bot(db.Model):
    __tablename__ = 'bots'

    bot_id = db.Column(db.Integer, primary_key = True)
    mac_ddr = db.Column(db.String(17), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey(users.user_id), nullable = True) # No es nullable porque si que peude existir un robot al que aun no se le ha asignado nignun usuario
    custom_name = db.Column(db.String(20), default = 'Focus-Bot') 
    passKey = db.Column(db.Text, nullable = False) # Passwd para identificarse durante la comunicación
    access_point = db.Column(db.String(150), nullable = False) # SSID generado por BOT
    last_sync = db.Column(db.DateTime)
    status = db.Column(sb.String(20), nullable=False, default=BotStatus.OFFLINE)
    finware_version = db.Column(db.String(20),nullable = True)

class ActivityState(enum.Enum):
    PENDIENTE = 'PENDIENTE'
    POSPUESTO = 'POSPUESTO'
    COMPLETADO = 'COMPLETADO'
    CANCELADO = 'CANCELADO'
    CURSO = 'EN CURSO'

class ActivityCategory (enum.Enum):
    ESTUDIOS = 'ESTUDIOS'
    LECTURA = 'LECTURA'
    HOGAR = 'HOGAR'
    DEPORTES = 'DEPORTES'
    DESCANSO = 'DESCANSO'
    OTRAS = 'OTRAS'

class ActivityResults (enum.Enum):
    COMPLETADO = 'COMPLETADO'
    PARCIAL = 'PARCIAL'
    FALLADO = 'FALLADO'

class Activity(db.Model):
    __tablename__ = 'activities'

    activity_id = db.Column(db.Integer, primary_key = True)
    type_id = db.Column(db.Integer, db.ForeignKey(activity_types.type_id), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey(users.user_id), nullable = False)
    bot_id = db.Column(db.Integer, db.ForeignKey(bots.bot_id), nullable = False)
    title = db.Column (db.String(50), nullable = False)
    description = db.Column (db.String(250))
    init_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    state = db.Column(db.String(20), nullable = False, default = ActivityState.PENDIENTE )
    category = db.Column(db.String(20), nullable = False, default = ActivityCategory.ESTUDIOS)
    result = db.Column(db.String(20), nullable = True)