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