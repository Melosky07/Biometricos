from django.urls import path,  include
from rest_framework.routers import DefaultRouter
from .views import RegistroAsistenciaViewSet, exportar_reporte_excel, obtener_datos, buscar_persona,generar_reporte_ausentes,generar_reporte_ausencias_semanal, generar_reporte_ausencias_historico

router = DefaultRouter()
router.register(r'registros', RegistroAsistenciaViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('reporte-excel/', exportar_reporte_excel, name='exportar_reporte_excel'),
    path('datos/', obtener_datos, name='obtener_datos'),
    path('buscar-persona/', buscar_persona, name='buscar_persona'),
    path('reporte-ausentes/', generar_reporte_ausentes, name='reporte-ausentes'),
    path('reporte-ausencias-semanal/', generar_reporte_ausencias_semanal, name='reporte-ausencias-semanal'),
    path('reporte-ausencias-historico/', generar_reporte_ausencias_historico, name='reporte_ausencias_historico'),
    ]