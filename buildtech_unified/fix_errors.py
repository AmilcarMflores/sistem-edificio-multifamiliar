#!/usr/bin/env python3
"""
Script para corregir automáticamente errores comunes en templates
"""
import os
import re

def fix_template_file(filepath):
    """Corregir errores en un archivo de template"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Corregir url_for sin blueprint
    # Mantener solo 'static' sin blueprint
    content = re.sub(
        r"url_for\(['\"](?!static|auth\.|mantenimiento\.|comunicacion\.|finanzas\.|reservas\.)(\w+)['\"]",
        r"url_for('auth.\1'",
        content
    )
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Corregido: {filepath}")
        return True
    return False

def main():
    templates_dir = '/home/amilcar/Documents/Desarrollo web/proyectos/sistem-edificio-multifamiliar/buildtech_unified/app/templates'
    
    fixed_count = 0
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                if fix_template_file(filepath):
                    fixed_count += 1
    
    print(f"\n✅ Archivos corregidos: {fixed_count}")

if __name__ == '__main__':
    main()
