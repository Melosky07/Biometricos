import pandas as pd
from asistencia.models import Persona
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Carga datos desde DB_Empleados.xlsx al modelo Persona'

    def handle(self, *args, **kwargs):
        archivo = 'C:/Users/anl-sistemas/Documents/Sebastian/App_Huelleros/backend/asistencia/BD_Empleados2.xlsx'  # <-- cambia esto

        try:
            df = pd.read_excel(archivo)

            for index, row in df.iterrows():
                nit = str(row['NIT']).replace('.', '').replace(' ', '').strip()
                nombre = str(row['Nombre']).strip()
                cargo = str(row['Nombre Cargo']).strip()
                dependencia = str(row['Nombre Dependencia']).strip()

                # Crear o actualizar la persona
                Persona.objects.update_or_create(
                    nit=nit,
                    defaults={
                        'nombre': nombre,
                        'cargo': cargo,
                        'dependencia': dependencia
                    }
                )

            self.stdout.write(self.style.SUCCESS("Carga completada correctamente."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ocurrió un error: {e}"))