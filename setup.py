# Script para configurar el entorno de desarrollo para el proyecto de misiles
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Configura el entorno de desarrollo para el proyecto"""
    print("🚀 Configurando entorno para el proyecto de simulación de misiles...")
    
    # Crear directorios necesarios
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    print(f"✅ Directorio de salida creado: {output_dir}")
    
    # Instalar dependencias
    print("📦 Instalando dependencias...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencias instaladas correctamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al instalar dependencias: {e}")
        return False
    
    # Verificar instalación de matplotlib y numpy
    try:
        import matplotlib
        import numpy
        print(f"✅ Matplotlib instalado: {matplotlib.__version__}")
        print(f"✅ NumPy instalado: {numpy.__version__}")
        print(f"🎨 Backend de Matplotlib: {matplotlib.get_backend()}")
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("   Ejecuta: pip install matplotlib numpy")
        return False
    
    print("\n✨ Entorno configurado. Para ejecutar el proyecto:")
    print("   python -m misiles.main --interactive")
    return True

if __name__ == "__main__":
    setup_environment()
