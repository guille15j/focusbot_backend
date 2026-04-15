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

    def to_dict(self):
        return {
            "result_id": self.result_id,
            "user_id": self.user_id,
            "init_date": self.init_date_range.strftime('%Y-%m-%d'),
            "end_date": self.end_date_range.strftime('%Y-%m-%d'),
            "num_completo": self.num_completo,
            "num_pendiente": self.num_pendiente,
            "most_category": self.most_category.name if self.most_category else None,
            "total_activities": self.total_activities,
            "total_used_time": str(self.total_used_time) # El Interval se lee mejor como string
        }

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
            "record": record.to_dict() 
        }, 201
    

    except Exception as e:
        db.session.rollback()
        return {"message" : "Error creando el record."}, 500
    
def cont_completado(lista):
    out = []

    for a in lista:
        if a.state == ActivityResults.SUCCESS:
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