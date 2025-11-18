#!/usr/bin/env python3
"""
Script para probar todas las rutas de la aplicación
"""
import requests
import sys

BASE_URL = "http://127.0.0.1:7000"

# Rutas públicas que deberían funcionar sin autenticación
PUBLIC_ROUTES = [
    "/",
    "/login",
]

# Rutas protegidas (esperamos redirección al login)
PROTECTED_ROUTES = [
    "/home",
    "/mantenimiento",
    "/comunicacion/chat",
    "/comunicacion/avisos",
    "/financiera/",
    "/reservas/",
]

def test_route(route, expected_redirect=False):
    """Probar una ruta específica"""
    try:
        response = requests.get(f"{BASE_URL}{route}", allow_redirects=False, timeout=5)
        
        if expected_redirect:
            if response.status_code in [301, 302, 303, 307, 308]:
                print(f"✓ {route:40} -> Redirige correctamente (protegida)")
                return True
            else:
                print(f"✗ {route:40} -> No redirige (código {response.status_code})")
                return False
        else:
            if response.status_code == 200:
                print(f"✓ {route:40} -> OK (200)")
                return True
            else:
                print(f"✗ {route:40} -> Error (código {response.status_code})")
                return False
    except requests.exceptions.RequestException as e:
        print(f"✗ {route:40} -> Error de conexión: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("PRUEBA DE RUTAS - BuildTech")
    print("="*70 + "\n")
    
    # Verificar que el servidor esté corriendo
    try:
        requests.get(BASE_URL, timeout=2)
    except:
        print("❌ Error: El servidor no está corriendo en", BASE_URL)
        print("   Ejecuta primero: python3 app/run.py")
        sys.exit(1)
    
    print("🔓 Rutas Públicas:")
    print("-" * 70)
    passed_public = sum(test_route(route) for route in PUBLIC_ROUTES)
    
    print(f"\n🔒 Rutas Protegidas (deben redirigir al login):")
    print("-" * 70)
    passed_protected = sum(test_route(route, expected_redirect=True) for route in PROTECTED_ROUTES)
    
    print("\n" + "="*70)
    total = len(PUBLIC_ROUTES) + len(PROTECTED_ROUTES)
    passed = passed_public + passed_protected
    print(f"RESULTADO: {passed}/{total} rutas funcionando correctamente")
    print("="*70 + "\n")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
