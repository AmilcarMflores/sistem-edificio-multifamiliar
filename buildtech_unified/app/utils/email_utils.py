# app/utils/email_utils.py
"""
Utilidades para envío de correos electrónicos
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Configuración de email (ajustar según necesites)
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_USER = 'tu_email@gmail.com'  # Cambiar
EMAIL_PASSWORD = 'tu_password_app'  # Cambiar por contraseña de aplicación
DEFAULT_FROM = 'BuildTech <buildtech@sistema.com>'

def enviar_email(destinatario, asunto, cuerpo_html, cuerpo_texto=None):
    """
    Envía un email
    
    Args:
        destinatario: Email del destinatario
        asunto: Asunto del email
        cuerpo_html: Cuerpo del mensaje en HTML
        cuerpo_texto: Cuerpo del mensaje en texto plano (opcional)
    
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['From'] = DEFAULT_FROM
        msg['To'] = destinatario
        msg['Subject'] = asunto
        
        # Agregar versión texto plano
        if cuerpo_texto:
            part1 = MIMEText(cuerpo_texto, 'plain', 'utf-8')
            msg.attach(part1)
        
        # Agregar versión HTML
        part2 = MIMEText(cuerpo_html, 'html', 'utf-8')
        msg.attach(part2)
        
        # Conectar y enviar
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, destinatario, msg.as_string())
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error al enviar email: {str(e)}")
        return False


def enviar_email_confirmacion_reserva(reserva):
    """
    Envía un email de confirmación de reserva
    """
    if not reserva.email:
        return False
    
    asunto = f"Confirmación de Reserva - {reserva.area.nombre}"
    
    cuerpo_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <h2 style="color: #0d6efd; text-align: center;">🎉 Reserva Confirmada</h2>
            
            <p>Estimado/a <strong>{reserva.usuario}</strong>,</p>
            
            <p>Tu reserva ha sido registrada exitosamente. A continuación los detalles:</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>📍 Área:</strong> {reserva.area.nombre}</p>
                <p><strong>📅 Fecha:</strong> {reserva.fecha.strftime('%d/%m/%Y')}</p>
                <p><strong>🕐 Horario:</strong> {reserva.hora_inicio.strftime('%H:%M')} - {reserva.hora_fin.strftime('%H:%M')}</p>
                <p><strong>👥 Personas:</strong> {reserva.num_personas}</p>
                <p><strong>💰 Costo:</strong> Bs. {reserva.costo_total:.2f}</p>
                <p><strong>📋 Estado:</strong> {reserva.estado.upper()}</p>
            </div>
            
            <p><strong>⚠️ Importante:</strong></p>
            <ul>
                <li>Recuerda realizar el pago antes de la fecha de tu reserva</li>
                <li>Llega 10 minutos antes del horario reservado</li>
                <li>Cuida las instalaciones y deja todo en orden</li>
            </ul>
            
            <p style="margin-top: 30px; text-align: center; color: #666;">
                <small>BuildTech - Sistema de Gestión Integral</small><br>
                <small>Este es un mensaje automático, por favor no responder</small>
            </p>
        </div>
    </body>
    </html>
    """
    
    cuerpo_texto = f"""
    CONFIRMACIÓN DE RESERVA
    
    Estimado/a {reserva.usuario},
    
    Tu reserva ha sido registrada exitosamente.
    
    DETALLES:
    - Área: {reserva.area.nombre}
    - Fecha: {reserva.fecha.strftime('%d/%m/%Y')}
    - Horario: {reserva.hora_inicio.strftime('%H:%M')} - {reserva.hora_fin.strftime('%H:%M')}
    - Personas: {reserva.num_personas}
    - Costo: Bs. {reserva.costo_total:.2f}
    - Estado: {reserva.estado.upper()}
    
    IMPORTANTE:
    - Recuerda realizar el pago antes de la fecha de tu reserva
    - Llega 10 minutos antes del horario reservado
    - Cuida las instalaciones y deja todo en orden
    
    BuildTech - Sistema de Gestión Integral
    """
    
    return enviar_email(reserva.email, asunto, cuerpo_html, cuerpo_texto)


def enviar_email_pago_confirmado(cargo_o_pago, tipo='cargo_mensual'):
    """
    Envía un email cuando se confirma un pago
    """
    # Implementar según necesidades
    pass


def enviar_email_recordatorio_pago(departamento, cargos_pendientes):
    """
    Envía un recordatorio de pagos pendientes
    """
    # Implementar según necesidades
    pass