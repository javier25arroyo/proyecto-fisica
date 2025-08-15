#!/usr/bin/env python3
"""
Demo del simulador de misiles simplificado.

Este archivo demuestra las dos opciones disponibles:
1. Simulación automática con configuración por defecto
2. Modo Juego intuitivo para niños

Uso:
    python3 demo_interfaz.py
"""

def main():
    print("🚀 DEMO - Simulador de Misiles")
    print("=" * 40)
    print()
    print("OPCIONES DISPONIBLES:")
    print()
    print("✅ 1. SIMULACIÓN AUTOMÁTICA")
    print("   - Configuración por defecto optimizada")
    print("   - Animación Rich en terminal")
    print("   - Cálculos automáticos de interceptación")
    print("   - Visualización profesional de trayectorias")
    print()
    print("✅ 2. MODO JUEGO (RECOMENDADO)")
    print("   - Interfaz simplificada tipo videojuego")
    print("   - Controles grandes y fáciles de usar")
    print("   - Misiones preconfiguradas con pistas")
    print("   - Terminología amigable para niños")
    print("   - Click en mapa para posicionar atacante")
    print("   - Botón grande '¡Defender!' para interceptar")
    print()
    print("CARACTERÍSTICAS DEL MODO JUEGO:")
    print("🎮 Controles simplificados: solo Fuerza y Ángulo")
    print("🎯 Interacción directa con el ratón")
    print("🚀 Misiones con dificultad progresiva")
    print("✨ Modo 'Auto' para ayuda automática")
    print("❓ Ayuda contextual integrada")
    print("🔄 Sistema de reinicio rápido")
    print()
    print("CÓMO USAR:")
    print("1. Ejecute: python3 -m misiles.main --interactive")
    print("2. Seleccione opción 1 o 2")
    print("3. ¡Disfrute de la física en acción!")
    print()
    
    try:
        from misiles.ui.game_mode import run_game
        print("📦 Módulos disponibles.")
        
        print("\n¿Qué opción desea probar?")
        print("1. Simulación automática")
        print("2. Modo Juego")
        print("3. Menú principal")
        
        choice = input("\nSeleccione (1, 2 o 3): ").strip()
        
        if choice == '1':
            print("\n🔬 Iniciando simulación automática...")
            from misiles.main import main_with_params
            main_with_params()
        elif choice == '2':
            print("\n🎮 Iniciando Modo Juego...")
            run_game()
        elif choice == '3':
            print("\n📋 Iniciando menú principal...")
            import subprocess
            import sys
            subprocess.run([sys.executable, "-m", "misiles.main", "--interactive"])
        else:
            print("💡 Use: python3 -m misiles.main --interactive")
            
    except ImportError as e:
        print(f"❌ Error al importar módulos: {e}")
        print("💡 Instale las dependencias: pip install matplotlib numpy")
        print("💡 Luego ejecute: python3 -m misiles.main --interactive")

if __name__ == "__main__":
    main()
