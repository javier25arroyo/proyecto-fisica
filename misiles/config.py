"""
Cargador de variables de entorno para el simulador de misiles.
Este módulo carga las variables de entorno desde el archivo .env
"""
import os
import sys
from pathlib import Path

def load_env():
    """
    Carga variables de entorno desde el archivo .env
    """
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        print(f"Advertencia: No se encontró el archivo .env en {env_path}")
        return {}
    
    env_vars = {}
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
                    # También establecer como variable de entorno del sistema
                    os.environ[key.strip()] = value.strip()
        
        return env_vars
    except Exception as e:
        print(f"Error al cargar el archivo .env: {e}")
        return {}

def get_env_var(name, default=None, type_cast=None):
    """
    Obtiene una variable de entorno con conversión de tipo opcional
    
    Args:
        name: Nombre de la variable de entorno
        default: Valor por defecto si no existe
        type_cast: Función para convertir el tipo (int, float, etc.)
    
    Returns:
        El valor de la variable de entorno o el valor por defecto
    """
    value = os.environ.get(name, default)
    if value is not None and type_cast is not None:
        try:
            value = type_cast(value)
        except (ValueError, TypeError):
            print(f"Advertencia: No se pudo convertir {name}='{value}' al tipo {type_cast.__name__}")
            return default
    return value

# Cargar variables de entorno al importar este módulo
ENV_VARS = load_env()

# Constantes importantes cargadas desde el entorno
GRAVITY = get_env_var('GRAVITY', 9.81, float)
DEFAULT_DT = get_env_var('DEFAULT_DT', 0.02, float)
SHOW_ANIMATIONS = get_env_var('SHOW_ANIMATIONS', '1') == '1'
DEBUG = get_env_var('DEBUG', '0') == '1'
OUTPUT_DIR = Path(get_env_var('OUTPUT_DIR', './output'))

# Crear el directorio de salida si no existe
OUTPUT_DIR.mkdir(exist_ok=True)

# Información para debugging
if DEBUG:
    print(f"Variables de entorno cargadas: {ENV_VARS}")
    print(f"GRAVITY: {GRAVITY}")
    print(f"DEFAULT_DT: {DEFAULT_DT}")
    print(f"SHOW_ANIMATIONS: {SHOW_ANIMATIONS}")
    print(f"OUTPUT_DIR: {OUTPUT_DIR}")
