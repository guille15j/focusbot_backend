from services import *
from utils import *
from operator import itemgetter
from datetime import timedelta

def calculateRecord(current_user, data):

    required_fields= ['init_date_range','end_date_range']

    if not all(field in data for field in required_fields):
        return {"message" : "Faltan los campos de fecha en la petición."} , 400

    list_activities = Activity.query.filter(
        Activity.user_id == current_user.user_id, 
        Activity.init_date.between(data['init_date_range'], data['end_date_range']),
        Activity.end_date.between(data['init_date_range'], data['end_date_range'])
    ).all()


    try:
        #Trabajamos con la lista de objetos para sacar las estadisiticas que necesitamos
        record = History(
            user_id = current_user.user_id,
            init_date_range = data['init_date_range'],
            end_date_range = data['end_date_range'],
            num_completo = cont_completado(list_activities),
            num_pospuesto = cont_pospuesto(list_activities),
            num_cancelado = cont_cancelado(list_activities),
            num_pendiente = cont_pendiente(list_activities),
            most_category = most_category(list_activities),
            total_activities = len(list_activities),
            total_used_time = calculate_totalTime(list_activities)
        )

        db.session.add(record)
        db.session.commit()

        return {
            "message": "Histórico creado con éxito", 
            "record": {
                'user_id': record.user_id,
                'init_date_range' : record.init_date_range,
                'end_date_range': record.end_date_range,
                'num_completo' : record.num_completo,
                'num_pospuesto' : record.num_pospuesto,
                'num_cancelado' : record.num_cancelado,
                'num_pendiente' : record.num_pendiente,
                'most_category' : record.most_category,
                'total_activities' : record.total_activities,
                'total_used_time' : record.total_used_time
            } 
        }, 201
    

    except Exception as e:
        db.session.rollback()
        return {"message" : "Error creando el record."}, 500
    
def cont_completado(lista):
    out = []

    for a in lista:
        if a.result == ActivityResults.SUCCESS:
            out.append(a)

    return len(out)

def cont_pospuesto(lista):
    out = []

    for a in lista:
        if a.state == ActivityState.POSPUESTO:
            out.append(a)

    return len(out)

def cont_cancelado(lista):
    out = []

    for a in lista:
        if a.state == ActivityState.CANCELADO:
            out.append(a)

    return len(out)

def cont_pendiente(lista):
    out = []

    for a in lista:
        if a.state == ActivityState.PENDIENTE:
            out.append(a)

    return len(out)

def most_category(lista):
    if not lista:
        return None
    
    dicc = {}

    for c in ActivityCategory.values():
        dicc [c] = 0

    for a in lista:
        dicc[a.category] += 1

    resultado = dict(sorted(dicc.items(), key=itemgetter(1), reverse=True))
        
    if not resultado:
        return None
    
    categoria_top = list(resultado.keys())[0]
    
    return categoria_top.value # Devolvemos la categoría con mejor cantidad

def calculate_totalTime(lista):
    total_time = timedelta()

    for a in lista:
        if a.end_date and a.init_date:
            total_time += (a.end_date - a.init_date)

    return total_time.total_seconds() / 60