# app/models/finanzas_model.py
"""
Modelos de Finanzas - Convertido de Django a Flask/SQLAlchemy
Gestión de cargos mensuales y pagos del edificio
"""

from database import db
from datetime import datetime, date
from decimal import Decimal

class CargoMensual(db.Model):
    """
    Cargos mensuales por departamento (luz, agua, gas, etc.)
    """
    __tablename__ = 'cargos_mensuales'
    
    id = db.Column(db.Integer, primary_key=True)
    departamento = db.Column(db.Integer, nullable=False, index=True)
    mes = db.Column(db.Integer, nullable=False)  # 1-12
    anio = db.Column(db.Integer, nullable=False)
    
    # Servicios básicos
    luz = db.Column(db.Numeric(10, 2), default=0.00)
    agua = db.Column(db.Numeric(10, 2), default=0.00)
    gas = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Otros cargos
    mantenimiento = db.Column(db.Numeric(10, 2), default=0.00)
    expensas_comunes = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Estado del pago
    pagado = db.Column(db.Boolean, default=False)
    fecha_pago = db.Column(db.Date, nullable=True)
    
    # Metadatos
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_vencimiento = db.Column(db.Date, nullable=True)
    
    def __init__(self, departamento, mes, anio, luz=0, agua=0, gas=0, 
                 mantenimiento=0, expensas_comunes=0):
        self.departamento = departamento
        self.mes = mes
        self.anio = anio
        self.luz = Decimal(str(luz))
        self.agua = Decimal(str(agua))
        self.gas = Decimal(str(gas))
        self.mantenimiento = Decimal(str(mantenimiento))
        self.expensas_comunes = Decimal(str(expensas_comunes))
        self.pagado = False
    
    @property
    def total(self):
        """Calcula el total del cargo"""
        return float(
            self.luz + self.agua + self.gas + 
            self.mantenimiento + self.expensas_comunes
        )
    
    @property
    def mes_nombre(self):
        """Retorna el nombre del mes"""
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        return meses[self.mes] if 1 <= self.mes <= 12 else 'Desconocido'
    
    def marcar_pagado(self):
        """Marca el cargo como pagado"""
        self.pagado = True
        self.fecha_pago = date.today()
        db.session.commit()
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    @staticmethod
    def get_by_id(cargo_id):
        return CargoMensual.query.get(cargo_id)
    
    @staticmethod
    def get_by_departamento(departamento):
        """Obtiene todos los cargos de un departamento"""
        return CargoMensual.query.filter_by(
            departamento=departamento
        ).order_by(CargoMensual.anio.desc(), CargoMensual.mes.desc()).all()
    
    @staticmethod
    def get_pendientes_by_departamento(departamento):
        """Obtiene cargos pendientes de un departamento"""
        return CargoMensual.query.filter_by(
            departamento=departamento,
            pagado=False
        ).order_by(CargoMensual.anio, CargoMensual.mes).all()
    
    @staticmethod
    def get_or_create_mes_actual(departamento):
        """Obtiene o crea el cargo del mes actual"""
        hoy = date.today()
        cargo = CargoMensual.query.filter_by(
            departamento=departamento,
            mes=hoy.month,
            anio=hoy.year
        ).first()
        
        if not cargo:
            cargo = CargoMensual(
                departamento=departamento,
                mes=hoy.month,
                anio=hoy.year
            )
            cargo.save()
        
        return cargo
    
    @staticmethod
    def get_all_pendientes():
        """Obtiene todos los cargos pendientes (para admin)"""
        return CargoMensual.query.filter_by(pagado=False).all()
    
    @staticmethod
    def get_total_recaudado_mes(mes, anio):
        """Calcula el total recaudado en un mes específico"""
        cargos = CargoMensual.query.filter_by(
            mes=mes,
            anio=anio,
            pagado=True
        ).all()
        
        total = sum(cargo.total for cargo in cargos)
        return float(total)


class PagoReserva(db.Model):
    """
    Pagos realizados por reservas de áreas comunes
    """
    __tablename__ = 'pagos_reservas'
    
    id = db.Column(db.Integer, primary_key=True)
    reserva_id = db.Column(db.Integer, db.ForeignKey('reservas.id'), nullable=False)
    
    # Información del pago
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    pagado = db.Column(db.Boolean, default=False)
    fecha_pago = db.Column(db.DateTime, nullable=True)
    
    # Método de pago
    metodo_pago = db.Column(db.String(50), nullable=True)
    # Valores posibles: 'efectivo', 'transferencia', 'tarjeta'
    
    # Referencia de pago
    referencia = db.Column(db.String(100), nullable=True)
    
    # Metadatos
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, reserva_id, monto):
        self.reserva_id = reserva_id
        self.monto = Decimal(str(monto))
        self.pagado = False
    
    def marcar_pagado(self, metodo_pago='efectivo', referencia=None):
        """Marca el pago como realizado"""
        self.pagado = True
        self.fecha_pago = datetime.utcnow()
        self.metodo_pago = metodo_pago
        self.referencia = referencia
        db.session.commit()
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    @staticmethod
    def get_by_id(pago_id):
        return PagoReserva.query.get(pago_id)
    
    @staticmethod
    def get_by_reserva(reserva_id):
        return PagoReserva.query.filter_by(reserva_id=reserva_id).first()
    
    @staticmethod
    def get_pendientes():
        """Obtiene todos los pagos pendientes"""
        return PagoReserva.query.filter_by(pagado=False).all()
    
    @staticmethod
    def get_total_recaudado_reservas(mes=None, anio=None):
        """Calcula el total recaudado por reservas"""
        query = PagoReserva.query.filter_by(pagado=True)
        
        if mes and anio:
            # Filtrar por mes/año si se proporciona
            from sqlalchemy import extract
            query = query.filter(
                extract('month', PagoReserva.fecha_pago) == mes,
                extract('year', PagoReserva.fecha_pago) == anio
            )
        
        pagos = query.all()
        total = sum(float(pago.monto) for pago in pagos)
        return total


class GastoEdificio(db.Model):
    """
    Gastos generales del edificio (mantenimiento, servicios, etc.)
    """
    __tablename__ = 'gastos_edificio'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Descripción del gasto
    concepto = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    
    # Monto
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Categoría
    categoria = db.Column(db.String(50), nullable=False)
    # Valores: 'mantenimiento', 'servicios', 'personal', 'equipamiento', 'otros'
    
    # Fecha del gasto
    fecha_gasto = db.Column(db.Date, nullable=False)
    
    # Metadatos
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    registrado_por = db.Column(db.String(100), nullable=True)
    
    def __init__(self, concepto, monto, categoria, fecha_gasto=None, 
                 descripcion=None, registrado_por=None):
        self.concepto = concepto
        self.monto = Decimal(str(monto))
        self.categoria = categoria
        self.fecha_gasto = fecha_gasto or date.today()
        self.descripcion = descripcion
        self.registrado_por = registrado_por
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    @staticmethod
    def get_by_id(gasto_id):
        return GastoEdificio.query.get(gasto_id)
    
    @staticmethod
    def get_all():
        return GastoEdificio.query.order_by(
            GastoEdificio.fecha_gasto.desc()
        ).all()
    
    @staticmethod
    def get_by_mes(mes, anio):
        """Obtiene gastos de un mes específico"""
        from sqlalchemy import extract
        return GastoEdificio.query.filter(
            extract('month', GastoEdificio.fecha_gasto) == mes,
            extract('year', GastoEdificio.fecha_gasto) == anio
        ).all()
    
    @staticmethod
    def get_total_mes(mes, anio):
        """Calcula el total de gastos de un mes"""
        gastos = GastoEdificio.get_by_mes(mes, anio)
        total = sum(float(gasto.monto) for gasto in gastos)
        return total
    
    @staticmethod
    def get_by_categoria(categoria):
        """Obtiene gastos por categoría"""
        return GastoEdificio.query.filter_by(categoria=categoria).all()


class HistorialPago(db.Model):
    """
    Historial de todos los pagos realizados (auditoría)
    """
    __tablename__ = 'historial_pagos'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Tipo de pago
    tipo_pago = db.Column(db.String(50), nullable=False)
    # Valores: 'cargo_mensual', 'reserva', 'otros'
    
    # Referencia al pago original
    objeto_id = db.Column(db.Integer, nullable=False)
    
    # Departamento que pagó
    departamento = db.Column(db.Integer, nullable=False)
    
    # Monto pagado
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Método de pago
    metodo_pago = db.Column(db.String(50), nullable=True)
    
    # Fecha del pago
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Observaciones
    observaciones = db.Column(db.Text, nullable=True)
    
    def __init__(self, tipo_pago, objeto_id, departamento, monto, 
                 metodo_pago='efectivo', observaciones=None):
        self.tipo_pago = tipo_pago
        self.objeto_id = objeto_id
        self.departamento = departamento
        self.monto = Decimal(str(monto))
        self.metodo_pago = metodo_pago
        self.observaciones = observaciones
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    @staticmethod
    def registrar_pago(tipo_pago, objeto_id, departamento, monto, 
                       metodo_pago='efectivo', observaciones=None):
        """Crea un registro en el historial"""
        historial = HistorialPago(
            tipo_pago=tipo_pago,
            objeto_id=objeto_id,
            departamento=departamento,
            monto=monto,
            metodo_pago=metodo_pago,
            observaciones=observaciones
        )
        historial.save()
        return historial
    
    @staticmethod
    def get_by_departamento(departamento):
        """Obtiene el historial de un departamento"""
        return HistorialPago.query.filter_by(
            departamento=departamento
        ).order_by(HistorialPago.fecha_pago.desc()).all()
    
    @staticmethod
    def get_all():
        return HistorialPago.query.order_by(
            HistorialPago.fecha_pago.desc()
        ).all()