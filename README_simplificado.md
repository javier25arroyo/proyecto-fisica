# Simulador de Misiles - Versión Simplificada

## Descripción

Simulador físico de interceptación de misiles con dos modos de uso:

1. **Simulación Automática**: Configuración por defecto con animación en terminal
2. **Modo Juego**: Interfaz gráfica intuitiva para niños

## Instalación

```bash
pip install matplotlib numpy
```

## Uso

### Opción 1: Menú Principal
```bash
python -m misiles.main --interactive
```

### Opción 2: Demo Interactivo
```bash
python demo_interfaz.py
```

### Opción 3: Simulación Automática Directa
```bash
python -m misiles.main
```

### Opción 4: Modo Juego Directo
```bash
python -c "from misiles.ui.game_mode import run_game; run_game()"
```

## Opciones Disponibles

### 1. Simulación Automática
- Configuración optimizada por defecto
- Cálculo automático de interceptación
- Animación Rich en terminal
- Sin intervención del usuario

### 2. Modo Juego (Recomendado)
- Interfaz gráfica simplificada
- Controles grandes tipo videojuego
- Solo dos parámetros: "Fuerza" y "Ángulo"
- Click en mapa para mover atacante
- Misiones preconfiguradas
- Ayuda integrada

## Características del Modo Juego

### Controles
- **💪 Fuerza**: Compresión del resorte (0.05-1.0m)
- **📐 Ángulo**: Ángulo de disparo (5°-85°)
- **🖱️ Click**: Posicionar atacante en el mapa

### Botones
- **🛡️ ¡Defender!**: Lanzar interceptación
- **🔄 Reiniciar**: Volver a configuración inicial
- **🎮 Siguiente misión**: Cambiar escenario
- **❓ Ayuda**: Mostrar instrucciones
- **✨ Auto**: Ajuste automático para interceptar

### Misiones
1. **Misión 1**: Interceptación básica
2. **Misión 2**: Misil rápido
3. **Misión 3**: Trayectoria alta

## Física Implementada

### Modelo de Resorte
```
v₀ = x × √(k/m)
```
- **x**: Compresión (Fuerza en el juego)
- **k**: Constante elástica
- **m**: Masa del proyectil

### Balística
- Trayectoria parabólica con gravedad
- Cálculo de punto de interceptación
- Optimización de ángulo y tiempo de disparo

### Parámetros del Sistema
- **Atacante**: k=20,000 N/m, m=10 kg
- **Defensor**: k=25,000 N/m, m=12 kg
- **Gravedad**: 9.81 m/s²

## Estructura del Proyecto

```
misiles/
├── core/                 # Lógica física
│   ├── springs.py       # Modelo de resortes
│   ├── physics.py       # Física básica
│   ├── trajectories.py  # Cálculo de trayectorias
│   └── intercept.py     # Algoritmo de interceptación
├── ui/                  # Interfaces de usuario
│   ├── game_mode.py     # Modo juego
│   ├── viz_rich.py      # Animación terminal
│   └── params.py        # Carga de configuración
├── scenarios/           # Configuraciones
│   └── baseline.json    # Escenario por defecto
└── main.py             # Punto de entrada
```

## Archivos Principales

- `main.py`: Menú principal y simulación automática
- `game_mode.py`: Interfaz gráfica del modo juego
- `demo_interfaz.py`: Demo interactivo
- `springs.py`: Física de resortes
- `intercept.py`: Algoritmo de interceptación

## Dependencias

- **matplotlib**: Interfaz gráfica
- **numpy**: Cálculos numéricos
- **rich**: Animación en terminal (incluida en Python 3.9+)

## Notas

- Las advertencias de emojis en matplotlib son normales y no afectan la funcionalidad
- El modo juego está optimizado para pantallas de 14" o mayores
- La interceptación siempre es posible ajustando automáticamente los parámetros del defensor
