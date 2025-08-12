from rest_framework import viewsets, status
from rest_framework.response import Response
from django.utils.timezone import localtime, now, localdate
from .models import Persona, RegistroAsistencia
from .serializers import RegistroAsistenciaSerializer
import csv
from django.http import HttpResponse, JsonResponse
import logging
import pandas as pd
import os
from datetime import timedelta, datetime
from io import BytesIO
# from django.conf import settings

logger = logging.getLogger(__name__)

EXCEL_FILE_PATH = os.path.join(os.path.dirname(__file__), 'BD_Empleados3.xlsx')


class RegistroAsistenciaViewSet(viewsets.ModelViewSet):
    queryset = RegistroAsistencia.objects.all()
    serializer_class = RegistroAsistenciaSerializer

    def create(self, request, *args, **kwargs):
        try:
            logger.info(f"Request data: {request.data}")
            nit = request.data.get('NIT')
            if not nit:
                return Response({"error": "El NIT es obligatorio"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                df = pd.read_excel(EXCEL_FILE_PATH, engine='openpyxl')
            except Exception as e:
                logger.error(f"Error al leer el archivo Excel: {str(e)}")
                return Response({"error": "Error al leer la base de datos (Excel)"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if 'NIT' not in df.columns or 'Nombre' not in df.columns:
                logger.error("El archivo Excel no tiene las columnas correctas")
                return Response({"error": "Archivo Excel incorrecto. Faltan columnas 'NIT' o 'Nombre'."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            df['NIT'] = df['NIT'].astype(str)
            persona_data = df.loc[df['NIT'] == str(nit)].to_dict(orient='records')

            if not persona_data:
                nombre = "No Registra"
                cargo = "No Registra"
                dependencia = "No Registra"
            else:
                nombre = persona_data[0].get('Nombre', 'No Registra')
                cargo = persona_data[0].get('Nombre Cargo', 'No Registra')
                dependencia = persona_data[0].get('Nombre Dependencia', 'No Registra')
                nit = str(nit)

        # Crear o actualizar la persona con cargo y dependencia
            persona, created = Persona.objects.update_or_create(
                nit=nit,
                defaults={'cargo': cargo, 'dependencia': dependencia, 'nombre': nombre}
            )

            hoy = now().date()
            registro = RegistroAsistencia.objects.filter(
                persona=persona,
                fecha=hoy,
                hora_salida__isnull=True
            ).first()

            if registro:
                registro.hora_salida = localtime(now()).time()
                registro.save()
                mensaje = f"Salida registrada para {nombre}"
            else:
                RegistroAsistencia.objects.create(
                    persona=persona,
                    hora_entrada=localtime(now()).time()
                )
                mensaje = f"Entrada registrada para {nombre}"

            registros = RegistroAsistencia.objects.all()
            serializer = self.get_serializer(registros, many=True)
            return Response({"mensaje": mensaje, "registros": serializer.data}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error en el backend: {str(e)}")
            return Response({"error": "Error interno en el servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def cargar_datos_excel():
    try:
        df = pd.read_excel(EXCEL_FILE_PATH, engine='openpyxl')
        return df
    except Exception as e:
        print(f"Error al cargar el archivo Excel: {e}")
        return None

def obtener_datos(request):
    df = cargar_datos_excel()
    if df is not None:
        data = df.to_dict(orient='records')
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'error': 'No se pudo cargar el archivo Excel'}, status=500)
    
def buscar_persona(request):
    nit = request.GET.get('NIT')
    if not nit:
        return JsonResponse({'error': 'El NIT es obligatorio'}, status=400)

    try:
        df = pd.read_excel(EXCEL_FILE_PATH)
        persona = df.loc[df['NIT'] == int(nit)].to_dict(orient='records')
        if persona:
            return JsonResponse(persona[0])
        else:
            return JsonResponse({
                'Nombre': 'No Registra',
                'Nombre Cargo': 'No Registra',
                'Nombre Dependencia': 'No Registra',
                'NIT': nit
            })
    except Exception as e:
        return JsonResponse({'error': f'Error al buscar en el archivo: {str(e)}'}, status=500)    

def exportar_reporte_excel(request):
    fecha_hoy = localdate().strftime("%Y-%m-%d")
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="reporte_asistencia_{fecha_hoy}.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(['NIT', 'Nombre', 'Cargo', 'Dependencia', 'Fecha', 'Hora Entrada', 'Hora Salida', 'Tiempo Trabajado'])

    registros = RegistroAsistencia.objects.select_related('persona').all()

    for registro in registros:
        writer.writerow([
            registro.persona.nit,
            registro.persona.nombre,
            registro.persona.cargo,
            registro.persona.dependencia,
            registro.fecha,
            registro.hora_entrada.strftime('%H:%M:%S'),
            registro.hora_salida.strftime('%H:%M:%S') if registro.hora_salida else '',
            registro.tiempo_trabajado(), 
        ])

    return response

def generar_reporte_ausentes(request):
    hoy = localdate()

    personas_presentes = RegistroAsistencia.objects.filter(fecha=hoy).values_list('persona__nit', flat=True).distinct()
    personas_ausentes = Persona.objects.exclude(nit__in=personas_presentes)

    data = [
        {
            'NIT': persona.nit,
            'Nombre': persona.nombre,
            'Cargo': persona.cargo,
            'Dependencia': persona.dependencia,
            'Estado': 'AUSENTE',
            'Fecha': hoy.strftime("%Y-%m-%d")
        }
        for persona in personas_ausentes
    ]

    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=ausentes_{hoy.strftime("%Y-%m-%d")}.xlsx'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Ausentes')

    return response

def generar_reporte_ausencias_semanal(request):
    hoy = localdate()
    dia_actual = hoy.weekday()  # lunes=0, domingo=6

    # Obtener el lunes de la semana actual (o anterior si es domingo)
    inicio_semana = hoy - timedelta(days=dia_actual + 7)
    dias_semana = [inicio_semana + timedelta(days=i) for i in range(7)]  # Lunes a Sábado

    personas = Persona.objects.all()
    data = []

    for persona in personas:
        fila = {
            'NIT': persona.nit,
            'Nombre': persona.nombre,
            'Cargo': persona.cargo,
            'Dependencia': persona.dependencia,
        }

        total_horas_semana = 0.0

        for dia in dias_semana:
            registros = RegistroAsistencia.objects.filter(persona=persona, fecha=dia)
            if registros.exists():
                registro = registros.first()  # Se asume un registro por día
                entrada = registro.hora_entrada.strftime('%H:%M') if registro.hora_entrada else ''
                salida = registro.hora_salida.strftime('%H:%M') if registro.hora_salida else ''

                if registro.hora_entrada and registro.hora_salida:
                    entrada_dt = datetime.combine(dia, registro.hora_entrada)
                    salida_dt = datetime.combine(dia, registro.hora_salida)
                    duracion = salida_dt - entrada_dt
                    total_segundos = int(duracion.total_seconds())
                    horas = total_segundos // 3600
                    minutos = (total_segundos % 3600) // 60

                    # Para sumar al total de la semana (en minutos)
                    total_horas_semana += total_segundos
                    fila[dia.strftime('%A')] = f"{entrada} - {salida} ({horas}h {minutos}min)"
                else:
                    fila[dia.strftime('%A')] = f"{entrada} - {salida} (0h)"
            else:
                fila[dia.strftime('%A')] = "❌"

        total_seg = int(total_horas_semana)
        total_horas = total_seg // 3600
        total_min = (total_seg % 3600) // 60
        fila["Total Horas Semana"] = f"{total_horas}h {total_min}min"
        data.append(fila)

    df = pd.DataFrame(data)

    # Renombrar los días al español
    df.rename(columns={
        'Monday': 'Lunes',
        'Tuesday': 'Martes',
        'Wednesday': 'Miércoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo',
    }, inplace=True)

    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    nombre_archivo = f"Reporte_semanal_{dias_semana[0]}_al_{dias_semana[-1]}.xlsx"

    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={nombre_archivo}'
    return response

def generar_reporte_ausencias_historico(request):
    hoy = localdate()
    personas = Persona.objects.all()
    fechas_registradas = RegistroAsistencia.objects.values_list('fecha', flat=True).distinct().order_by('fecha')
    data = []

    for persona in personas:
        for fecha in fechas_registradas:
            registros = RegistroAsistencia.objects.filter(persona=persona, fecha=fecha)
            if registros.exists():
                registro = registros.first()
                entrada = registro.hora_entrada.strftime('%H:%M') if registro.hora_entrada else ''
                salida = registro.hora_salida.strftime('%H:%M') if registro.hora_salida else ''
                tiempo_trabajado = ''
                if registro.hora_entrada and registro.hora_salida:
                    entrada_dt = datetime.combine(fecha, registro.hora_entrada)
                    salida_dt = datetime.combine(fecha, registro.hora_salida)
                    duracion = salida_dt - entrada_dt
                    total_segundos = int(duracion.total_seconds())
                    horas = total_segundos // 3600
                    minutos = (total_segundos % 3600) // 60
                    tiempo_trabajado = f"{horas}h {minutos}min"
                else:
                    tiempo_trabajado = "0h 0min"
                
                data.append({
                    'Fecha': fecha.strftime("%Y-%m-%d"),
                    'NIT': persona.nit,
                    'Nombre': persona.nombre,
                    'Cargo': persona.cargo,
                    'Dependencia': persona.dependencia,
                    'Hora Entrada': entrada,
                    'Hora Salida': salida,
                    'Horas Trabajadas': tiempo_trabajado
                })
            else:
                data.append({
                    'Fecha': fecha.strftime("%Y-%m-%d"),
                    'NIT': persona.nit,
                    'Nombre': persona.nombre,
                    'Cargo': persona.cargo,
                    'Dependencia': persona.dependencia,
                    'Hora Entrada': '',
                    'Hora Salida': '',
                    'Horas Trabajadas': '❌ AUSENTE'
                })

    df = pd.DataFrame(data)

    # ✅ Solo una escritura en BytesIO usando ExcelWriter
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Ausentes Históricos')

    output.seek(0)

    ruta = os.path.join(os.getcwd(), "archivo_prueba.xlsx")
    with open(ruta, "wb") as f:
        f.write(output.getvalue())

    print("Archivo guardado en:", ruta)

    nombre_archivo = f"Reporte_historico_al_{hoy.strftime('%Y-%m-%d')}.xlsx"
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={nombre_archivo}'

    return response