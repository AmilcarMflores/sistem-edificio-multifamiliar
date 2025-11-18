
from django.contrib import admin
from django.urls import path
from build import views as usuarios_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', usuarios_views.login_view, name='login'),
    path('home/', usuarios_views.home, name='home'),
    path('reservas/', usuarios_views.reservas, name='reservas'),
    path('reservas_admin/', usuarios_views.reservas_admin, name='reservas_admin'),
    path('eliminar_reserva/<int:reserva_id>/', usuarios_views.eliminar_reserva, name='eliminar_reserva'),
    path('editar_reserva/<int:reserva_id>/', usuarios_views.editar_reserva, name='editar_reserva'),
    path('fechas_ocupadas/<int:area_id>/', usuarios_views.fechas_ocupadas, name='fechas_ocupadas'),
    path('horarios_disponibles/<int:area_id>/', usuarios_views.horarios_disponibles, name='horarios_disponibles'),
    path('cargos_pendientes/dpto/<int:departamento_id>/', usuarios_views.calcular_cargos_mensuales, name='calcular_cargos_mensuales'),
    path('pagar_cargo/dpto/<int:departamento_id>/<str:tipo_cargo>/<int:objeto_id>/', usuarios_views.pagar_cargo_pendiente, name='pagar_cargo_pendiente'),
    path('financiera/', usuarios_views.resumen_financiero, name='resumen_financiero'),
    path('financiera/pagar/<str:tipo_pago>/<int:pk>/', usuarios_views.pagar_pendiente, name='pagar_pendiente'),
]
