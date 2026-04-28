import smtplib
import os
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


def generar_codigo_verificacion():
    """
    Genera un código numérico aleatorio de 6 dígitos.
    
    - Rango: 100000 a 999999 (1 millón de combinaciones).
    - Se usa para verificación de email en plataformas web, iOS y Android.
    - El código se almacena en la BD y expira en 10 minutos.
    """
    return str(random.randint(100000, 999999))


def enviar_correo_verificacion(destinatario, codigo):
    """
    Envía un código de verificación de 6 dígitos por correo electrónico.
    
    - Compatible con web, iOS y Android: el usuario copia el código y lo pega en la app.
    - El código expira en 10 minutos.
    - Se envía en texto plano y HTML para compatibilidad con todos los clientes.
    """
    
    remitente = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')
    
    # Versión texto plano
    cuerpo_texto = f'''
    FocusApp - Verificación de cuenta
    
    Tu código de verificación es: {codigo}
    
    Introduce este código en la aplicación para activar tu cuenta.
    Este código expirará en 10 minutos.
    
    Si no has creado una cuenta en FocusApp, ignora este mensaje.
    '''
    
    # Versión HTML con diseño adaptativo (funciona en móvil y escritorio)
    cuerpo_html = f'''
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">FocusApp - Verificación de cuenta</h2>
        <p>Introduce el siguiente código en la aplicación para activar tu cuenta:</p>
        
        <!-- Código grande y centrado, fácil de leer en móvil -->
        <div style="background-color: #f5f5f5; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
            <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #4CAF50;">{codigo}</span>
        </div>
        
        <p style="color: #666; font-size: 14px;">Este código expirará en <strong>10 minutos</strong>.</p>
        <p style="color: #666; font-size: 14px;">Si no has creado una cuenta en FocusApp, ignora este mensaje.</p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">Este es un correo automático, por favor no respondas a este mensaje.</p>
    </body>
    </html>
    '''
    
    # Construir mensaje multiparte
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Código de verificación - FocusApp'
    msg['From'] = remitente
    msg['To'] = destinatario
    
    parte_texto = MIMEText(cuerpo_texto, 'plain', 'utf-8')
    parte_html = MIMEText(cuerpo_html, 'html', 'utf-8')
    msg.attach(parte_texto)
    msg.attach(parte_html)
    
    # Enviar usando SMTP con TLS
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls()
            servidor.login(remitente, password)
            servidor.sendmail(remitente, destinatario, msg.as_string())
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False