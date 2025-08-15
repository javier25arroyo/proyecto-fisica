# Script para configurar el entorno de desarrollo para el proyecto de misiles
import os
import sys
import subprocess
import platform
from pathlib import Path

def setup_environment():
    """Configura el entorno de desarrollo para el proyecto"""
    print("🚀 Configurando entorno para el proyecto de simulación de misiles...")
    
    # Detectar sistema operativo
    system = platform.system()
    print(f"Sistema operativo detectado: {system}")
    
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
    
    # Verificar instalación de matplotlib
    try:
        import matplotlib
        print(f"✅ Matplotlib instalado: versión {matplotlib.__version__}")
    except ImportError:
        print("❌ No se pudo importar matplotlib. Por favor, instala manualmente con:")
        print("   pip install matplotlib")
        return False
    
    # Verificar instalación de numpy
    try:
        import numpy
        print(f"✅ NumPy instalado: versión {numpy.__version__}")
    except ImportError:
        print("❌ No se pudo importar numpy. Por favor, instala manualmente con:")
        print("   pip install numpy")
        return False
    
    # Información sobre backend de matplotlib
    try:
        print(f"🎨 Backend de Matplotlib: {matplotlib.get_backend()}")
        print("   Si tienes problemas con las animaciones, puedes cambiar el backend en el archivo .env")
    except Exception:
        pass
    
    print("\n✨ Entorno configurado. Para ejecutar el proyecto:")
    print("   python -m misiles.main --interactive")
    return True

if __name__ == "__main__":
    setup_environment()
