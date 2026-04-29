from services.db_service import db, Activity, ActivityState, ActivityCategory, ActivityResults, History
from utils import *
from operator import itemgetter
from datetime import timedelta
from sqlalchemy import or_, and_

def calculateRecord(current_user, data):

    required_fields= ['init_date_range','end_date_range']

    if not all(field in data for field in required_fields):
        return {"message" : "Faltan los campos de fecha en la petición."} , 400

    list_activities = Activity.query.filter(
        Activity.user_id == current_user.user_id, 
        or_(
            and_(Activity.init_date >= data['init_date_range'], Activity.init_date <= data['end_date_range']),
            and_(Activity.end_date >= data['init_date_range'], Activity.end_date <= data['end_date_range']),
            and_(Activity.init_date <= data['init_date_range'], Activity.end_date >= data['end_date_range'])
        )
    ).all()


    try:
        n_sucess = 0
        n_pospuesto = 0
        n_cancelado = 0
        n_pendiente = 0

        categorias = {}
        for c in ActivityCategory:
            categorias [c] = 0

        total_time = timedelta()

        for v in list_activities:
            if v.result == ActivityResults.SUCCESS:
                n_sucess+=1

            if v.state == ActivityState.POSPUESTO:
                n_pospuesto += 1

            if v.state == ActivityState.CANCELADO:
                n_cancelado += 1

            if v.state == ActivityState.PENDIENTE:
                n_pendiente += 1

            if v.end_date and v.init_date:
                total_time += (v.end_date - v.init_date)

            categorias[v.category] += 1

        resultado = dict(sorted(categorias.items(), key=itemgetter(1), reverse=True))
        if not resultado:
            categoria_top = None
        else:
            categoria_top = list(resultado.keys())[0]

        total_time_value = total_time.total_seconds() / 60
        categoria_top_value = categoria_top.value if categoria_top else None

        #Trabajamos con la lista de objetos para sacar las estadisiticas que necesitamos
        record = History(
            user_id = current_user.user_id,
            init_date_range = data['init_date_range'],
            end_date_range = data['end_date_range'],
            num_completo = n_sucess,
            num_pospuesto = n_pospuesto,
            num_cancelado = n_cancelado,
            num_pendiente = n_pendiente,
            most_category = categoria_top_value,
            total_activities = len(list_activities),
            total_used_time = total_time_value
        )

        db.session.add(record)
        db.session.commit()

        return {
            "message": "Histórico creado con éxito", 
            "record": {
                'user_id': record.user_id,
                'init_date_range': record.init_date_range.isoformat(),
                'end_date_range': record.end_date_range.isoformat(),
                'num_completo' : record.num_completo,
                'num_pospuesto' : record.num_pospuesto,
                'num_cancelado' : record.num_cancelado,
                'num_pendiente' : record.num_pendiente,
                'most_category': record.most_category.value if record.most_category else None,
                'total_activities' : record.total_activities,
                'total_used_time' : record.total_used_time
            } 
        }, 201
    

    except Exception as e:
        db.session.rollback()
        return {"message" : "Error creando el record."}, 500
    
def recordByID(current_user, record_id):
    record = History.query.filter(History.record_id == record_id,
                                   History.user_id == current_user.user_id
    ).first()

    if not record:
        return {"message" : "No se ha encontrado el record en el sistema."} , 404
    
    record_out = {
        'user_id': record.user_id,
        'init_date_range': record.init_date_range.isoformat(),
        'end_date_range': record.end_date_range.isoformat(),
        'num_completo' : record.num_completo,
        'num_pospuesto' : record.num_pospuesto,
        'num_cancelado' : record.num_cancelado,
        'num_pendiente' : record.num_pendiente,
        'most_category': record.most_category.value if record.most_category else None,
        'total_activities' : record.total_activities,
        'total_used_time' : record.total_used_time
    } 

    return {"record": record_out}, 200

def getAllRecords (current_user):
    list_records = History.query.filter(History.user_id == current_user.user_id).all()

    records_out = []
    for r in list_records:
        records_out.append({
            'record_id': r.record_id,
            'user_id': r.user_id,
            'init_date_range': r.init_date_range.isoformat(),
            'end_date_range': r.end_date_range.isoformat(),
            'num_completo': r.num_completo,
            'num_pospuesto': r.num_pospuesto,
            'num_cancelado': r.num_cancelado,
            'num_pendiente': r.num_pendiente,
            'most_category': r.most_category.value if r.most_category else None,
            'total_activities': r.total_activities,
            'total_used_time': r.total_used_time
        })

    return {"records": records_out}, 200