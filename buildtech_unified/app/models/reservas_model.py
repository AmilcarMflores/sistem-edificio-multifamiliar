# app/models/reservas_model.py
"""
Modelos de Reservas - Convertido de Django a Flask/SQLAlchemy
Gestión de reservas de áreas comunes del edificio
"""

from database import db
from datetime import datetime, date, time, timedelta
from decimal import Decimal

class AreaComun(db.Model):
    """
    Áreas comunes disponibles para reserva
    """
    __tablename__ = 'areas_comunes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.Text, nullable=True)
    
    # Capacidad y características
    capacidad = db.Column(db.Integer, default=0)
    
    # Disponibilidad
    disponible = db.Column(db.Boolean, default=True)
    
    # Costo por hora
    costo_hora = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Horario de operación
    hora_apertura = db.Column(db.Time, default=time(8, 0))
    hora_cierre = db.Column(db.Time, default=time(22, 0))
    
    # Tiempo mínimo y máximo de reserva (en horas)
    tiempo_minimo = db.Column(db.Integer, default=1)
    tiempo_maximo = db.Column(db.Integer, default=8)
    
    # Metadatos
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con reservas
    reservas = db.relationship('Reserva', backref='area', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, nombre, descripcion=None, capacidad=0, costo_hora=0, 
                 hora_apertura=None, hora_cierre=None):
        self.nombre = nombre
        self.descripcion = descripcion
        self.capacidad = capacidad
        self.costo_hora = Decimal(str(costo_hora))
        self.hora_apertura = hora_apertura or time(8, 0)
        self.hora_cierre = hora_cierre or time(22, 0)
        self.disponible = True
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    @staticmethod
    def get_by_id(area_id):
        return AreaComun.query.get(area_id)
    
    @staticmethod
    def get_all():
        return AreaComun.query.all()
    
    @staticmethod
    def get_disponibles():
        """Obtiene solo áreas disponibles"""
        return AreaComun.query.filter_by(disponible=True).all()
    
    def esta_disponible_en(self, fecha, hora_inicio, hora_fin):
        """Verifica si el área está disponible en un horario específico"""
        # Verificar si el área está habilitada
        if not self.disponible:
            return False
        
        # Verificar horario de operación
        if hora_inicio < self.hora_apertura or hora_fin > self.hora_cierre:
            return False
        
        # Verificar si hay reservas conflictivas
        from sqlalchemy import and_, or_
        conflictos = Reserva.query.filter(
            and_(
                Reserva.area_id == self.id,
                Reserva.fecha == fecha,
                Reserva.estado.in_(['pendiente', 'confirmada']),
                or_(
                    # La nueva reserva empieza durante una existente
                    and_(
                        Reserva.hora_inicio <= hora_inicio,
                        Reserva.hora_fin > hora_inicio
                    ),
                    # La nueva reserva termina durante una existente
                    and_(
                        Reserva.hora_inicio < hora_fin,
                        Reserva.hora_fin >= hora_fin
                    ),
                    # La nueva reserva contiene una existente
                    and_(
                        Reserva.hora_inicio >= hora_inicio,
                        Reserva.hora_fin <= hora_fin
                    )
                )
            )
        ).first()
        
        return conflictos is None


class Reserva(db.Model):
    """
    Reservas de áreas comunes
    """
    __tablename__ = 'reservas'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relación con área común
    area_id = db.Column(db.Integer, db.ForeignKey('areas_comunes.id'), nullable=False)
    
    # Departamento que reserva
    departamento = db.Column(db.Integer, nullable=False, index=True)
    
    # Información del usuario que reserva
    usuario = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    
    # Fecha y horario de la reserva
    fecha = db.Column(db.Date, nullable=False, index=True)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    
    # Motivo de la reserva
    motivo = db.Column(db.String(200), nullable=True)
    
    # Cantidad de personas
    num_personas = db.Column(db.Integer, default=1)
    
    # Costo total
    costo_total = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Estado de la reserva
    estado = db.Column(db.String(20), default='pendiente')
    # Estados: 'pendiente', 'confirmada', 'cancelada', 'completada'
    
    # Metadatos
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Observaciones
    observaciones = db.Column(db.Text, nullable=True)
    
    def __init__(self, area_id, departamento, usuario, fecha, hora_inicio, hora_fin,
                 motivo=None, num_personas=1, telefono=None, email=None):
        self.area_id = area_id
        self.departamento = departamento
        self.usuario = usuario
        self.fecha = fecha
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.motivo = motivo
        self.num_personas = num_personas
        self.telefono = telefono
        self.email = email
        self.estado = 'pendiente'
        
        # Calcular costo
        self.calcular_costo()
    
    def calcular_costo(self):
        """Calcula el costo total de la reserva"""
        area = AreaComun.get_by_id(self.area_id)
        if area:
            # Calcular horas de reserva
            hora_inicio_dt = datetime.combine(date.today(), self.hora_inicio)
            hora_fin_dt = datetime.combine(date.today(), self.hora_fin)
            horas = (hora_fin_dt - hora_inicio_dt).total_seconds() / 3600
            
            self.costo_total = float(area.costo_hora) * horas
    
    @property
    def duracion_horas(self):
        """Calcula la duración en horas"""
        hora_inicio_dt = datetime.combine(date.today(), self.hora_inicio)
        hora_fin_dt = datetime.combine(date.today(), self.hora_fin)
        return (hora_fin_dt - hora_inicio_dt).total_seconds() / 3600
    
    def confirmar(self):
        """Confirma la reserva"""
        self.estado = 'confirmada'
        db.session.commit()
    
    def cancelar(self, motivo=None):
        """Cancela la reserva"""
        self.estado = 'cancelada'
        if motivo:
            self.observaciones = motivo
        db.session.commit()
    
    def completar(self):
        """Marca la reserva como completada"""
        self.estado = 'completada'
        db.session.commit()
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    @staticmethod
    def get_by_id(reserva_id):
        return Reserva.query.get(reserva_id)
    
    @staticmethod
    def get_all():
        return Reserva.query.order_by(Reserva.fecha.desc(), Reserva.hora_inicio.desc()).all()
    
    @staticmethod
    def get_by_departamento(departamento):
        """Obtiene todas las reservas de un departamento"""
        return Reserva.query.filter_by(
            departamento=departamento
        ).order_by(Reserva.fecha.desc()).all()
    
    @staticmethod
    def get_proximas_by_departamento(departamento):
        """Obtiene las próximas reservas de un departamento"""
        hoy = date.today()
        return Reserva.query.filter(
            Reserva.departamento == departamento,
            Reserva.fecha >= hoy,
            Reserva.estado.in_(['pendiente', 'confirmada'])
        ).order_by(Reserva.fecha, Reserva.hora_inicio).all()
    
    @staticmethod
    def get_by_area(area_id):
        """Obtiene todas las reservas de un área"""
        return Reserva.query.filter_by(area_id=area_id).order_by(Reserva.fecha.desc()).all()
    
    @staticmethod
    def get_by_fecha(fecha):
        """Obtiene todas las reservas de una fecha específica"""
        return Reserva.query.filter_by(fecha=fecha).all()
    
    @staticmethod
    def get_pendientes():
        """Obtiene todas las reservas pendientes"""
        return Reserva.query.filter_by(estado='pendiente').all()
    
    @staticmethod
    def get_fechas_ocupadas(area_id, mes=None, anio=None):
        """
        Obtiene las fechas que tienen al menos una reserva confirmada
        para un área específica
        """
        query = Reserva.query.filter(
            Reserva.area_id == area_id,
            Reserva.estado.in_(['pendiente', 'confirmada'])
        )
        
        if mes and anio:
            from sqlalchemy import extract
            query = query.filter(
                extract('month', Reserva.fecha) == mes,
                extract('year', Reserva.fecha) == anio
            )
        
        reservas = query.all()
        fechas = set(r.fecha for r in reservas)
        return sorted(list(fechas))
    
    @staticmethod
    def get_horarios_disponibles(area_id, fecha):
        """
        Retorna los horarios disponibles para una fecha específica
        """
        area = AreaComun.get_by_id(area_id)
        if not area or not area.disponible:
            return []
        
        # Obtener reservas del día
        reservas_dia = Reserva.query.filter(
            Reserva.area_id == area_id,
            Reserva.fecha == fecha,
            Reserva.estado.in_(['pendiente', 'confirmada'])
        ).order_by(Reserva.hora_inicio).all()
        
        # Generar horarios disponibles (bloques de 1 hora)
        horarios_disponibles = []
        hora_actual = area.hora_apertura
        
        while hora_actual < area.hora_cierre:
            # Calcular hora fin del bloque
            hora_fin = (datetime.combine(date.today(), hora_actual) + timedelta(hours=1)).time()
            
            # Verificar si hay conflicto con alguna reserva
            conflicto = False
            for reserva in reservas_dia:
                if not (hora_fin <= reserva.hora_inicio or hora_actual >= reserva.hora_fin):
                    conflicto = True
                    break
            
            if not conflicto:
                horarios_disponibles.append({
                    'hora_inicio': hora_actual.strftime('%H:%M'),
                    'hora_fin': hora_fin.strftime('%H:%M')
                })
            
            # Avanzar al siguiente bloque
            hora_actual = hora_fin
        
        return horarios_disponibles


# Función helper para inicializar áreas comunes por defecto
def inicializar_areas_comunes():
    """Crea áreas comunes predeterminadas si no existen"""
    areas_default = [
        {
            'nombre': 'Salón de Fiestas',
            'descripcion': 'Amplio salón para eventos y celebraciones',
            'capacidad': 50,
            'costo_hora': 100.00
        },
        {
            'nombre': 'Salón de Reuniones',
            'descripcion': 'Sala equipada para reuniones y presentaciones',
            'capacidad': 20,
            'costo_hora': 50.00
        },
        {
            'nombre': 'Piscina',
            'descripcion': 'Piscina climatizada',
            'capacidad': 30,
            'costo_hora': 75.00,
            'hora_apertura': time(9, 0),
            'hora_cierre': time(20, 0)
        },
        {
            'nombre': 'Área de Parrillas',
            'descripcion': 'Zona de parrillas al aire libre',
            'capacidad': 25,
            'costo_hora': 40.00
        },
        {
            'nombre': 'Cancha Deportiva',
            'descripcion': 'Cancha multiuso para deportes',
            'capacidad': 20,
            'costo_hora': 30.00
        }
    ]
    
    for area_data in areas_default:
        # Verificar si ya existe
        existe = AreaComun.query.filter_by(nombre=area_data['nombre']).first()
        if not existe:
            area = AreaComun(**area_data)
            area.save()
            print(f"✅ Área creada: {area_data['nombre']}")