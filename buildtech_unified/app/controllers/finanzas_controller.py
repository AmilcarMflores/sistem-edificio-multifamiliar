# app/controllers/finanzas_controller.py
"""
Controlador de Finanzas - Convertido de Django views a Flask
Gestión de cargos mensuales, pagos y resumen financiero
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from utils.decorators import role_required
from models.finanzas_model import CargoMensual, PagoReserva, GastoEdificio, HistorialPago
from models.reservas_model import Reserva
from datetime import date, datetime
from decimal import Decimal

finanzas_bp = Blueprint('finanzas', __name__, url_prefix='/financiera')

@finanzas_bp.route('/')
@role_required('admin')
def resumen_financiero():
    """
    Vista del resumen financiero general (solo admin)
    """
    hoy = date.today()
    mes_actual = hoy.month
    anio_actual = hoy.year
    
    # Obtener cargos mensuales
    cargos_pendientes = CargoMensual.get_all_pendientes()
    total_pendiente_cargos = sum(cargo.total for cargo in cargos_pendientes)
    
    # Obtener pagos de reservas pendientes
    pagos_reservas_pendientes = PagoReserva.get_pendientes()
    total_pendiente_reservas = sum(float(pago.monto) for pago in pagos_reservas_pendientes)
    
    # Calcular ingresos del mes actual
    ingresos_cargos = CargoMensual.get_total_recaudado_mes(mes_actual, anio_actual)
    ingresos_reservas = PagoReserva.get_total_recaudado_reservas(mes_actual, anio_actual)
    total_ingresos = ingresos_cargos + ingresos_reservas
    
    # Calcular gastos del mes actual
    gastos_mes = GastoEdificio.get_by_mes(mes_actual, anio_actual)
    total_gastos = sum(float(gasto.monto) for gasto in gastos_mes)
    
    # Balance
    balance = total_ingresos - total_gastos
    
    # Historial reciente
    historial_reciente = HistorialPago.get_all()[:10]
    
    context = {
        'mes_actual': datetime(anio_actual, mes_actual, 1).strftime('%B %Y'),
        'total_pendiente_cargos': total_pendiente_cargos,
        'total_pendiente_reservas': total_pendiente_reservas,
        'cargos_pendientes': cargos_pendientes,
        'pagos_reservas_pendientes': pagos_reservas_pendientes,
        'ingresos_cargos': ingresos_cargos,
        'ingresos_reservas': ingresos_reservas,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'balance': balance,
        'gastos_mes': gastos_mes,
        'historial_reciente': historial_reciente
    }
    
    return render_template('finanzas/resumen.html', **context)


@finanzas_bp.route('/cargos_mensuales/dpto/<int:departamento_id>/')
@login_required
def calcular_cargos_mensuales(departamento_id):
    """
    Vista de cargos mensuales de un departamento específico
    Accesible por el residente del departamento o por admin
    """
    # Verificar permisos
    if not current_user.has_role('admin'):
        if current_user.departamento != departamento_id:
            flash('No tienes permiso para ver esta información.', 'danger')
            return redirect(url_for('auth.home'))
    
    # Obtener o crear cargo del mes actual
    cargo_mes_actual = CargoMensual.get_or_create_mes_actual(departamento_id)
    
    # Obtener todos los cargos pendientes
    cargos_pendientes = CargoMensual.get_pendientes_by_departamento(departamento_id)
    
    # Obtener historial de pagos
    historial = HistorialPago.get_by_departamento(departamento_id)
    
    # Obtener pagos de reservas pendientes
    reservas_pendientes = []
    if hasattr(current_user, 'departamento') and current_user.departamento == departamento_id:
        reservas = Reserva.get_by_departamento(departamento_id)
        for reserva in reservas:
            pago = PagoReserva.get_by_reserva(reserva.id)
            if pago and not pago.pagado:
                reservas_pendientes.append({
                    'reserva': reserva,
                    'pago': pago
                })
    
    # Calcular totales
    total_pendiente = sum(cargo.total for cargo in cargos_pendientes)
    total_reservas_pendiente = sum(item['pago'].monto for item in reservas_pendientes)
    
    context = {
        'departamento': departamento_id,
        'cargo_mes_actual': cargo_mes_actual,
        'cargos_pendientes': cargos_pendientes,
        'reservas_pendientes': reservas_pendientes,
        'historial': historial,
        'total_pendiente': total_pendiente,
        'total_reservas_pendiente': float(total_reservas_pendiente),
        'total_general_pendiente': total_pendiente + float(total_reservas_pendiente)
    }
    
    return render_template('finanzas/cargos_departamento.html', **context)


@finanzas_bp.route('/pagar/cargo/<int:departamento_id>/<string:tipo_cargo>/<int:objeto_id>/', 
                    methods=['GET', 'POST'])
@login_required
def pagar_cargo_pendiente(departamento_id, tipo_cargo, objeto_id):
    """
    Procesar el pago de un cargo pendiente
    tipo_cargo puede ser: 'cargo_mensual' o 'reserva'
    """
    # Verificar permisos
    if not current_user.has_role('admin'):
        if current_user.departamento != departamento_id:
            flash('No tienes permiso para realizar esta acción.', 'danger')
            return redirect(url_for('auth.home'))
    
    if tipo_cargo == 'cargo_mensual':
        cargo = CargoMensual.get_by_id(objeto_id)
        if not cargo:
            flash('Cargo no encontrado.', 'danger')
            return redirect(url_for('finanzas.calcular_cargos_mensuales', 
                                  departamento_id=departamento_id))
        
        if cargo.pagado:
            flash('Este cargo ya fue pagado.', 'info')
            return redirect(url_for('finanzas.calcular_cargos_mensuales', 
                                  departamento_id=departamento_id))
        
        if request.method == 'POST':
            metodo_pago = request.form.get('metodo_pago', 'efectivo')
            
            # Marcar como pagado
            cargo.marcar_pagado()
            
            # Registrar en historial
            HistorialPago.registrar_pago(
                tipo_pago='cargo_mensual',
                objeto_id=objeto_id,
                departamento=departamento_id,
                monto=cargo.total,
                metodo_pago=metodo_pago,
                observaciones=f'Pago de cargo mensual {cargo.mes_nombre} {cargo.anio}'
            )
            
            flash(f'Pago registrado exitosamente. Monto: Bs. {cargo.total:.2f}', 'success')
            return redirect(url_for('finanzas.calcular_cargos_mensuales', 
                                  departamento_id=departamento_id))
        
        context = {
            'tipo_pago': 'Cargo Mensual',
            'descripcion': f'{cargo.mes_nombre} {cargo.anio}',
            'monto': cargo.total,
            'objeto': cargo,
            'departamento': departamento_id,
            'tipo_cargo': tipo_cargo,
            'objeto_id': objeto_id
        }
        
        return render_template('finanzas/pagar_pendiente.html', **context)
    
    elif tipo_cargo == 'reserva':
        pago = PagoReserva.get_by_id(objeto_id)
        if not pago:
            flash('Pago de reserva no encontrado.', 'danger')
            return redirect(url_for('finanzas.calcular_cargos_mensuales', 
                                  departamento_id=departamento_id))
        
        if pago.pagado:
            flash('Esta reserva ya fue pagada.', 'info')
            return redirect(url_for('finanzas.calcular_cargos_mensuales', 
                                  departamento_id=departamento_id))
        
        # Obtener la reserva asociada
        reserva = Reserva.get_by_id(pago.reserva_id)
        
        if request.method == 'POST':
            metodo_pago = request.form.get('metodo_pago', 'efectivo')
            referencia = request.form.get('referencia', '')
            
            # Marcar como pagado
            pago.marcar_pagado(metodo_pago=metodo_pago, referencia=referencia)
            
            # Registrar en historial
            HistorialPago.registrar_pago(
                tipo_pago='reserva',
                objeto_id=pago.reserva_id,
                departamento=departamento_id,
                monto=pago.monto,
                metodo_pago=metodo_pago,
                observaciones=f'Pago de reserva - {reserva.area.nombre if reserva else "Área desconocida"}'
            )
            
            flash(f'Pago de reserva registrado exitosamente. Monto: Bs. {pago.monto:.2f}', 'success')
            return redirect(url_for('finanzas.calcular_cargos_mensuales', 
                                  departamento_id=departamento_id))
        
        context = {
            'tipo_pago': 'Reserva',
            'descripcion': f'{reserva.area.nombre if reserva else "Área"} - {reserva.fecha if reserva else ""}',
            'monto': float(pago.monto),
            'objeto': pago,
            'reserva': reserva,
            'departamento': departamento_id,
            'tipo_cargo': tipo_cargo,
            'objeto_id': objeto_id
        }
        
        return render_template('finanzas/pagar_pendiente.html', **context)
    
    else:
        flash('Tipo de cargo no válido.', 'danger')
        return redirect(url_for('finanzas.calcular_cargos_mensuales', 
                              departamento_id=departamento_id))


@finanzas_bp.route('/pagar/<string:tipo_pago>/<int:pk>/', methods=['POST'])
@role_required('admin')
def pagar_pendiente(tipo_pago, pk):
    """
    Marcar un pago como realizado (ruta rápida para admin desde el resumen)
    """
    if tipo_pago == 'cargo':
        cargo = CargoMensual.get_by_id(pk)
        if cargo and not cargo.pagado:
            cargo.marcar_pagado()
            HistorialPago.registrar_pago(
                tipo_pago='cargo_mensual',
                objeto_id=pk,
                departamento=cargo.departamento,
                monto=cargo.total,
                observaciones=f'Pago procesado por admin'
            )
            flash('Cargo marcado como pagado.', 'success')
        else:
            flash('Cargo no encontrado o ya pagado.', 'warning')
    
    elif tipo_pago == 'reserva':
        pago = PagoReserva.get_by_id(pk)
        if pago and not pago.pagado:
            reserva = Reserva.get_by_id(pago.reserva_id)
            pago.marcar_pagado()
            HistorialPago.registrar_pago(
                tipo_pago='reserva',
                objeto_id=pago.reserva_id,
                departamento=reserva.departamento if reserva else 0,
                monto=pago.monto,
                observaciones=f'Pago procesado por admin'
            )
            flash('Pago de reserva marcado como pagado.', 'success')
        else:
            flash('Pago no encontrado o ya realizado.', 'warning')
    
    return redirect(url_for('finanzas.resumen_financiero'))


@finanzas_bp.route('/gastos/', methods=['GET', 'POST'])
@role_required('admin')
def gestionar_gastos():
    """
    Gestionar gastos del edificio
    """
    if request.method == 'POST':
        concepto = request.form.get('concepto')
        monto = request.form.get('monto')
        categoria = request.form.get('categoria')
        fecha_gasto_str = request.form.get('fecha_gasto')
        descripcion = request.form.get('descripcion')
        
        try:
            fecha_gasto = datetime.strptime(fecha_gasto_str, '%Y-%m-%d').date()
        except:
            fecha_gasto = date.today()
        
        gasto = GastoEdificio(
            concepto=concepto,
            monto=float(monto),
            categoria=categoria,
            fecha_gasto=fecha_gasto,
            descripcion=descripcion,
            registrado_por=current_user.get_full_name()
        )
        gasto.save()
        
        flash('Gasto registrado exitosamente.', 'success')
        return redirect(url_for('finanzas.gestionar_gastos'))
    
    # GET
    gastos = GastoEdificio.get_all()
    
    return render_template('finanzas/gastos.html', gastos=gastos)


@finanzas_bp.route('/api/resumen_mes/<int:mes>/<int:anio>')
@role_required('admin')
def api_resumen_mes(mes, anio):
    """
    API para obtener resumen financiero de un mes específico
    """
    ingresos_cargos = CargoMensual.get_total_recaudado_mes(mes, anio)
    ingresos_reservas = PagoReserva.get_total_recaudado_reservas(mes, anio)
    gastos = GastoEdificio.get_total_mes(mes, anio)
    
    return jsonify({
        'ingresos_cargos': ingresos_cargos,
        'ingresos_reservas': ingresos_reservas,
        'total_ingresos': ingresos_cargos + ingresos_reservas,
        'gastos': gastos,
        'balance': (ingresos_cargos + ingresos_reservas) - gastos
    })