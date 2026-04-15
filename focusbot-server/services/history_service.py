from services import *
from utils import *
from operator import itemgetter

def calculateRecord(current_user, data):

    required_fields= ['init_date_range','end_date_range']

    if not all(field in data for field in required_fields):
        return {"message" : "Faltan los campos de fecha en la petición."} , 500

    list_activities = Activity.query.filter(
        Activity.user_id == current_user.user_id, 
        Activity.init_date.between(data['init_date_range'], data['end_date_range']),
        Activity.end_date.between(data['init_date_range'], data['end_date_range'])
    ).all()

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

    try:
        db.session.add(record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {"message" : "Error creando el record."}, 500
    


    return {"message": "Historico creado con éxito", "record" : record}, 201

def cont_completado(list):
    out = []

    for a in list:
        if a.state == ActivityResults.SUCCESS:
            out.append(a)

    return len(out)

def cont_pospuesto(list):
    out = []

    for a in list:
        if a.state == ActivityState.POSPUESTO:
            out.append(a)

    return len(out)

def cont_cancelado(list):
    out = []

    for a in list:
        if a.state == ActivityState.CANCELADO:
            out.append(a)

    return len(out)

def cont_pendiente(list):
    out = []

    for a in list:
        if a.state == ActivityState.PENDIENTE:
            out.append(a)

    return len(out)

def most_category(lit):

    dicc = {}

    for c in ActivityCategory.values():
        dicc [c] = 0

    for a in list:
        dicc[a.category] += 1

    resultado = dict(sorted(dicc.items(), key=itemgetter(1), reverse=True))
        
    if not resultado:
        return None
    
    categoria_top = list(resultado.keys())[0]
    
    return categoria_top.value # Devolvemos la categoría con mejor cantidad

def calculate_totalTime(list):
    total_time = 0.0

    for a in list:
        if a.end_date and a.init_date:
            total_time += (a.end_date - a.init_date)

    return total_time