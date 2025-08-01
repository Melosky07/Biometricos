from django.db import models
from datetime import datetime, timedelta

class Persona(models.Model):
    nombre = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100, null=True, blank=True)
    dependencia = models.CharField(max_length=100, null=True, blank=True)
    nit = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.nombre

class RegistroAsistencia(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField(null=True, blank=True)

    def tiempo_trabajado(self):
        if self.hora_entrada and self.hora_salida:
            entrada = datetime.combine(self.fecha, self.hora_entrada)
            salida = datetime.combine(self.fecha, self.hora_salida)
            duracion = salida - entrada
            total_segundos = int(duracion.total_seconds())
            horas = total_segundos // 3600
            minutos = (total_segundos % 3600) // 60
            segundos = total_segundos % 60
            return f'{horas:02}:{minutos:02}:{segundos:02}'  # Formato hh:mm:ss
        return ''

    def __str__(self):
        return f'{self.nombre} - {self.fecha}'