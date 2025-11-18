import os
import json

# Ruta relativa al archivo apartamentos.json
APARTAMENTOS_FILE = os.path.join('usuarios', 'data', 'apartamentos.json')

def migrar():
    if not os.path.exists(APARTAMENTOS_FILE):
        print("❌ El archivo no existe:", os.path.abspath(APARTAMENTOS_FILE))
        return

    # Cargar datos
    with open(APARTAMENTOS_FILE, 'r', encoding='utf-8') as f:
        apartamentos = json.load(f)

    # Migrar cada apartamento
    for apt in apartamentos:
        # Si tiene 'propietario' como string, convertir a lista
        if 'propietario' in apt and isinstance(apt['propietario'], str) and apt['propietario'].strip():
            apt['propietarios'] = [apt['propietario'].strip()]
            del apt['propietario']
        # Si no tiene 'propietarios', crear lista vacía
        if 'propietarios' not in apt:
            apt['propietarios'] = []

    # Guardar cambios
    with open(APARTAMENTOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(apartamentos, f, indent=4, ensure_ascii=False)

    print("✅ Migración completada. Ahora 'propietarios' es una lista.")

if __name__ == '__main__':
    migrar()