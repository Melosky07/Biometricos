from rest_framework import serializers
from .models import RegistroAsistencia, Persona

class RegistroAsistenciaSerializer(serializers.ModelSerializer):
    persona_nombre = serializers.CharField(source='persona.nombre', read_only=True)
    hora_entrada = serializers.SerializerMethodField()
    hora_salida = serializers.SerializerMethodField()
    tiempo_trabajado = serializers.SerializerMethodField()
    cargo = serializers.CharField(source='persona.cargo', read_only=True)
    dependencia = serializers.CharField(source='persona.dependencia', read_only=True)
    nit = serializers.CharField(source='persona.nit', read_only=True)

    class Meta:
        model = RegistroAsistencia
        fields = ['id', 'fecha', 'hora_entrada', 'hora_salida', 'tiempo_trabajado', 'persona_nombre', 'cargo', 'dependencia', 'nit']


    def get_hora_entrada(self, obj):
        if obj.hora_entrada:
            return obj.hora_entrada.strftime('%H:%M:%S')
        return None

    def get_hora_salida(self, obj):
        if obj.hora_salida:
            return obj.hora_salida.strftime('%H:%M:%S')
        return None

    def get_tiempo_trabajado(self, obj):
        return obj.tiempo_trabajado() if obj.tiempo_trabajado() else ''