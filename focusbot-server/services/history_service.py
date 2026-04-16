from services.db_service import db, Activity, ActivityState, ActivityCategory, ActivityResults, History
from utils import *
from operator import itemgetter
from datetime import timedelta

def calculateRecord(current_user, data):

    required_fields= ['init_date_range','end_date_range']

    if not all(field in data for field in required_fields):
        return {"message" : "Faltan los campos de fecha en la petición."} , 400

    list_activities = Activity.query.filter(
        Activity.user_id == current_user.user_id, 
        db.or_(
            db.and_(Activity.init_date >= data['init_date_range'], Activity.init_date <= data['end_date_range']),
            db.and_(Activity.end_date >= data['init_date_range'], Activity.end_date <= data['end_date_range']),
            db.and_(Activity.init_date <= data['init_date_range'], Activity.end_date >= data['end_date_range'])
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
                'most_category' : record.most_category,
                'total_activities' : record.total_activities,
                'total_used_time' : record.total_used_time
            } 
        }, 201
    

    except Exception as e:
        db.session.rollback()
        return {"message" : "Error creando el record."}, 500
    
# def cont_completado(lista):
#     out = []
#     for a in lista:
#         if a.result == ActivityResults.SUCCESS:
#             out.append(a)
#     return len(out)
# def cont_pospuesto(lista):
#     out = []
#     for a in lista:
#         if a.state == ActivityState.POSPUESTO:
#             out.append(a)
#     return len(out)
# def cont_cancelado(lista):
#     out = []
#     for a in lista:
#         if a.state == ActivityState.CANCELADO:
#             out.append(a)
#     return len(out)
# def cont_pendiente(lista):
#     out = []
#     for a in lista:
#         if a.state == ActivityState.PENDIENTE:
#             out.append(a)
#     return len(out)
# def most_category(lista):
#     if not lista:
#         return None  
#     dicc = {}
#     for c in ActivityCategory.values():
#         dicc [c] = 0
#     for a in lista:
#         dicc[a.category] += 1
#     resultado = dict(sorted(dicc.items(), key=itemgetter(1), reverse=True))      
#     if not resultado:
#         return None   
#     categoria_top = list(resultado.keys())[0]  
#     return categoria_top.value # Devolvemos la categoría con mejor cantidad
# def calculate_totalTime(lista):
#     total_time = timedelta()
#     for a in lista:
#         if a.end_date and a.init_date:
#             total_time += (a.end_date - a.init_date)
#     return total_time.total_seconds() / 60