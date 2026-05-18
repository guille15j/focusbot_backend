from datetime import timedelta, datetime
from operator import itemgetter
from sqlalchemy import or_, and_
from services.db_service import db, Activity, ActivityState, ActivityCategory, ActivityResults, History
from utils import *

def calculateRecord(current_user, data):
    """
    Generador de reportes persistentes con el tiempo con rangos de fecha libres otorgador
    por el usuario desde la apalicación. Se almacenarán en la base de datos y podran ser 
    consultados desde la app.
    Calculará:
        - init_date_range (Fecha): Inicio del periodo seleccionado (ej. lunes de la semana de exámenes).

        - end_date_range (Fecha): Fin del periodo seleccionado.

        - num_completo (Entero): Cantidad de actividades cuyo Estado pasó a completado.

        - num_pospuesto (Entero): Cantidad de actividades cuyo Estado pasó a pospuesto.

        - num_cancelado (Entero): Cantidad de actividades cuyo Estado pasó a cancelado.

        - total_activities (Entero): El volumen total de actividades procesadas en ese rango. Es crucial para que tu modal calcule la Tasa de éxito: (num_completo / total_activities) * 100.

        - total_used_time (Entero): Suma total de minutos calculados a través de las diferencias de tiempo.

        - most_category (String): El nombre exacto de la categoría (ej. "ESTUDIOS") para que el modal pinte el icono de la escuela en verde.
    """
    required_fields = ['init_date_range', 'end_date_range']

    if not all(field in data for field in required_fields):
        return {"message": "Faltan los campos de fecha en la petición."}, 400

    try:
        # 1. Normalización estricta de las fechas límites
        if isinstance(data['init_date_range'], str):
            init_range = datetime.fromisoformat(data['init_date_range'].replace('Z', ''))
            end_range = datetime.fromisoformat(data['end_date_range'].replace('Z', ''))
        else:
            init_range = data['init_date_range']
            end_range = data['end_date_range']

        # Forzamos límites diarios completos (00:00:00.000 a 23:59:59.999)
        init_range = init_range.replace(hour=0, minute=0, second=0, microsecond=0)
        end_range = end_range.replace(hour=23, minute=59, second=59, microsecond=999999)

        # 2. Filtro Base: Solo actividades con fechas de ejecución en el rango
        # Esto excluye automáticamente las PENDIENTES que no tienen fechas
        list_activities = Activity.query.filter(
            Activity.user_id == current_user.user_id,
            or_(
                and_(Activity.init_date >= init_range, Activity.init_date <= end_range),
                and_(Activity.end_date >= init_range, Activity.end_date <= end_range),
                and_(Activity.init_date <= init_range, Activity.end_date >= end_range)
            )
        ).all()

        # 3. Inicialización de contadores de Estado y Resultados
        n_sucess = 0       # Resultado de efectividad (Calidad)
        n_completo = 0     # Estado: Completado (Volumen)
        n_pospuesto = 0    # Estado: Pospuesto
        n_cancelado = 0    # Estado: Cancelado

        categorias = {c.name: 0 for c in ActivityCategory}
        total_time = timedelta()

        # 4. Procesamiento de los datos del informe
        for v in list_activities:
            v_result_str = (v.result.name if hasattr(v.result, 'name') else str(v.result)).upper()
            v_state_str = (v.state.name if hasattr(v.state, 'name') else str(v.state)).upper()

            # Conteo de Resultado (Efectividad)
            if v.result == ActivityResults.SUCCESS or v_result_str == "SUCCESS":
                n_sucess += 1

            # Conteo de Estados independientes
            if v_state_str in ["COMPLETADO", "COMPLETADA", "FINALIZADO", "TERMINADO"]:
                n_completo += 1
            elif v.state == ActivityState.POSPUESTO or v_state_str == "POSPUESTO":
                n_pospuesto += 1
            elif v.state == ActivityState.CANCELADO or v_state_str == "CANCELADO":
                n_cancelado += 1

            # Acumulación de tiempo invertido
            if v.end_date and v.init_date:
                total_time += (v.end_date - v.init_date)

            # Mapeo de categorías
            if v.category:
                cat_name = v.category.name if hasattr(v.category, 'name') else str(v.category)
                if cat_name in categorias:
                    categorias[cat_name] += 1

        # 5. Determinación de la categoría top
        resultado_cat = dict(sorted(categorias.items(), key=itemgetter(1), reverse=True))
        if not list_activities or max(categorias.values()) == 0:
            categoria_top_str = "OTRAS"
        else:
            top_key = list(resultado_cat.keys())[0]
            # Si top_key es un objeto Enum, extraemos su string (.name), si no, lo convertimos
            categoria_top_str = top_key.name if hasattr(top_key, 'name') else str(top_key)

        total_time_minutes = int(total_time.total_seconds() / 60)
        
        # El total de actividades evaluadas en la tasa de éxito del informe
        total_valid_activities = n_completo + n_pospuesto + n_cancelado

        # 6. Persistencia en Base de Datos
        record = History(
            user_id = current_user.user_id,
            init_date_range = init_range,
            end_date_range = end_range,
            num_completo = n_completo,
            num_pospuesto = n_pospuesto,
            num_cancelado = n_cancelado,
            num_pendiente = 0,  
            most_category = categoria_top_str, # <--- Pasamos el texto limpio aquí
            total_activities = total_valid_activities,
            total_used_time = total_time_minutes
        )

        db.session.add(record)
        db.session.commit()

        # 7. Formateo de respuesta
        return {
            "message": "Histórico creado con éxito", 
            "record": {
                'record_id': record.record_id,
                'user_id': record.user_id,
                'init_date_range': record.init_date_range.isoformat(),
                'end_date_range': record.end_date_range.isoformat(),
                'num_completo': record.num_completo,
                'num_pospuesto': record.num_pospuesto,
                'num_cancelado': record.num_cancelado,
                'num_pendiente': record.num_pendiente,
                'most_category': record.most_category.name if hasattr(record.most_category, 'name') else str(record.most_category),
                'total_activities': record.total_activities,
                'total_used_time': record.total_used_time
            } 
        }, 201

    except Exception as e:
        db.session.rollback()
        print(f"Error en el Endpoint de informes: {str(e)}")
        return {"message": "Error interno del servidor al procesar el histórico."}, 500

def getWeeklyDashboard(current_user):
    """
    Generador de reportes semanales volatiles. No se almacenan, representan el porgreso del usuario
    durante la semana en curso de L a D. Alimentará el grafico de barras apiladas y los KPIs.
    Calculará:
    - total_completados (Entero): Suma de todas las tareas completadas esta semana.

    - total_used_time (Entero): Minutos totales invertidos esta semana.

    - top_category (String): La categoría que más veces se ha repetido esta semana.

    - day (String): La letra correspondiente ('L', 'M', 'X', 'J', 'V', 'S', 'D').

    - completado (Entero): Actividades completadas únicamente en ese día.

    - normal (Entero): Actividades pendientes únicamente en ese día (nota: tu gráfica mapea normal al color de Pendiente).

    - cancelado (Entero): Actividades canceladas únicamente en ese día.

    - hasValue (Booleano): true si ese día el usuario tuvo alguna actividad interactuada/creada, o false si el día está completamente vacío (para que la barra se muestre semitransparente como dicta tu estilo).
    """
    try:
        # 1. Cálculo automático de la semana en curso (Lunes a Domingo)
        today = datetime.now()
        current_day = today.weekday()  # 0 = Lunes, 6 = Domingo
        
        # Calculamos el lunes de esta semana a las 00:00:00
        monday_of_week = today - timedelta(days=current_day)
        monday_of_week = monday_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calculamos el domingo de esta semana a las 23:59:59
        sunday_of_week = monday_of_week + timedelta(days=6)
        sunday_of_week = sunday_of_week.replace(hour=23, minute=59, second=59, microsecond=999999)

        # 2. CONSULTA A: Actividades con movimientos/fechas esta semana
        executed_activities = Activity.query.filter(
            Activity.user_id == current_user.user_id,
            or_(
                and_(Activity.init_date >= monday_of_week, Activity.init_date <= sunday_of_week),
                and_(Activity.end_date >= monday_of_week, Activity.end_date <= sunday_of_week)
            )
        ).all()

        # 3. CONSULTA B: Total de pendientes del usuario (Global sin fecha)
        v_state_pendiente_str = "PENDIENTE"
        total_pendientes_actuales = Activity.query.filter(
            Activity.user_id == current_user.user_id,
            or_(
                Activity.state == ActivityState.PENDIENTE,
                Activity.state == v_state_pendiente_str
            )
        ).count()

        # 4. Inicialización de la estructura del Gráfico de Barras Apiladas (Bloque B)
        # 0=L, 1=M, 2=X, 3=J, 4=V, 5=S, 6=D
        weekdays_letters = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
        chart_days_map = {
            i: {"day": weekdays_letters[i], "completado": 0, "normal": 0, "cancelado": 0, "hasValue": False}
            for i in range(7)
        }

        # Variables para los KPIs Generales (Bloque A)
        total_completados_semana = 0
        total_time_semana = timedelta()
        categorias_semana = {c.name: 0 for c in ActivityCategory}

        # 5. Distribución de datos en los cajones de la semana
        for v in executed_activities:
            v_state_str = (v.state.name if hasattr(v.state, 'name') else str(v.state)).upper()

            # Determinamos qué fecha usar de anclaje para posicionar el registro en la semana
            target_date = v.end_date if v.end_date else v.init_date
            if not target_date:
                continue
                
            day_index = target_date.weekday() # Obtiene el índice 0-6 del día

            if 0 <= day_index <= 6:
                chart_days_map[day_index]["hasValue"] = True

                # Clasificación estricta según tus requerimientos de frontend
                if v_state_str in ["COMPLETADO", "COMPLETADA", "FINALIZADO", "TERMINADO"]:
                    chart_days_map[day_index]["completado"] += 1
                    total_completados_semana += 1
                    
                    # El tiempo invertido solo computa a las completadas con éxito de ejecución
                    if v.end_date and v.init_date:
                        total_time_semana += (v.end_date - v.init_date)

                elif v_state_str in ["POSPUESTO", "POSPUESTA"]:
                    # Mapeamos los Pospuestos al campo "normal" que tu gráfica pinta con el color primario
                    chart_days_map[day_index]["normal"] += 1

                elif v_state_str in ["CANCELADO", "CANCELADA"]:
                    chart_days_map[day_index]["cancelado"] += 1

                # Mapeo de categorías de la semana
                if v.category:
                    cat_name = v.category.name if hasattr(v.category, 'name') else str(v.category)
                    if cat_name in categorias_semana:
                        categorias_semana[cat_name] += 1

        # 6. Resolución de Categoría Top de la semana
        resultado_cat = dict(sorted(categorias_semana.items(), key=itemgetter(1), reverse=True))
        if not executed_activities or max(categorias_semana.values()) == 0:
            top_category_semana = "Sin registros"
        else:
            top_category_semana = list(resultado_cat.keys())[0]

        total_minutes_semana = int(total_time_semana.total_seconds() / 60)

        # 7. Construcción del JSON estructurado final
        return {
            "summary": {
                "total_completados": total_completados_semana,
                "total_used_time": total_minutes_semana,
                "top_category": top_category_semana,
                "total_pendientes_actuales": total_pendientes_actuales  # El KPI guardado bajo la manga
            },
            "weekChartData": list(chart_days_map.values())
        }, 200

    except Exception as e:
        print(f"Error en el Endpoint de Dashboard Semanal: {str(e)}")
        return {"message": "Error interno al calcular la tendencia semanal."}, 500

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