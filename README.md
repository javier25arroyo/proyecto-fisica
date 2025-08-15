# Simulador de Misiles

## Descripción

Simulador físico de interceptación de misiles con dos modos de uso:

1. **Simulación Automática**: Configuración por defecto con animación en terminal
2. **Modo Juego**: Interfaz gráfica intuitiva para niños

## Instalación

### Opción 1: Instalación automática con script de configuración
```bash
python setup.py
```
Este script instalará todas las dependencias necesarias y configurará el entorno automáticamente.

### Opción 2: Instalación manual de dependencias
```bash
pip install -r requirements.txt
```

### Opción 3: Instalación básica
```bash
pip install matplotlib numpy rich
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

## 🎮 Características del Modo Juego

### 🕹️ Controles Principales

#### 💪 **FUERZA** (Compresión del Resorte)
🔧 **¿Qué es?** La distancia que comprimes un resorte antes de disparar
📏 **Rango:** 0.05m (muy suave) ↔ 1.0m (máxima potencia)
🎯 **Efecto:** 
- ⬆️ **Más Fuerza** = Misil más rápido y mayor alcance
- ⬇️ **Menos Fuerza** = Misil más lento y menor distancia

💡 **Analogía:** Como estirar la cuerda de un arco - mientras más la estires, más lejos va la flecha

#### 📐 **ÁNGULO** (Dirección de Disparo)
🎯 **¿Qué es?** La inclinación hacia arriba del misil al disparar
📏 **Rango:** 5° (casi horizontal) ↔ 85° (casi vertical)
🎯 **Efecto:**
- 🏹 **45°** = Máximo alcance (el ángulo perfecto)
- ⬇️ **Ángulos bajos** (15°-30°) = Trayectoria plana y rápida
- ⬆️ **Ángulos altos** (60°-80°) = Trayectoria alta y lenta

💡 **Analogía:** Como lanzar una pelota - 45° es perfecto para llegar más lejos

#### 🖱️ **POSICIONAMIENTO**
🎯 **Click en el mapa** para mover el lanzador rojo a cualquier posición
📍 **Coordenadas** se actualizan automáticamente

### 🎲 Botones de Control
- **🛡️ ¡Defender!**: Lanza la interceptación automática
- **🔄 Reiniciar**: Vuelve a la configuración inicial de la misión
- **🎮 Siguiente misión**: Cambia al próximo escenario de dificultad
- **❓ Ayuda**: Muestra instrucciones detalladas en consola
- **✨ Auto**: Ajuste automático del defensor para garantizar interceptación

### 🎯 Misiones Disponibles
1. **🥇 Misión 1**: Interceptación básica - ¡Tu primera defensa!
2. **🥈 Misión 2**: Misil súper rápido - ¡Reacciona rápido!
3. **🥉 Misión 3**: Trayectoria alta - ¡Apunta hacia el cielo!

## 🧮 Física Implementada

### ⚡ **Fórmula de Velocidad del Resorte**
```
v₀ = x × √(k/m)
```

#### 🔍 **Explicación de Cada Variable:**

| Variable | Emoji | Significado | Valor Típico | Efecto |
|----------|-------|-------------|--------------|---------|
| **v₀** | 🚀 | Velocidad inicial del misil | 22-45 m/s | ⬆️ Más rápido = más lejos |
| **x** | 💪 | Compresión del resorte (FUERZA) | 0.05-1.0 m | ⬆️ Más compresión = más velocidad |
| **k** | 🔧 | Rigidez del resorte | 20,000 N/m | ⬆️ Más rígido = más potente |
| **m** | ⚖️ | Masa del proyectil | 10 kg | ⬇️ Más pesado = más lento |

### 🎯 **Fórmula de Interceptación**

El simulador calcula automáticamente:

#### 📐 **Ángulo Óptimo del Defensor:**
```
θ_defensor = arctan(vy/vx) en el punto de encuentro
```

#### ⏱️ **Tiempo de Interceptación:**
```
t_intercept = tiempo cuando proyectiles se encuentran
```

#### 📍 **Punto de Encuentro:**
```
x_encuentro = x₀ + v₀x × t
y_encuentro = y₀ + v₀y × t - ½gt²
```

### 🔬 **Variables de la Interceptación:**

| Variable | Emoji | Significado | Función |
|----------|-------|-------------|---------|
| **θ** | 📐 | Ángulo de disparo | Controla la dirección |
| **g** | 🌍 | Gravedad terrestre (9.81 m/s²) | Hace que los misiles caigan |
| **t** | ⏱️ | Tiempo de vuelo | Cuánto tarda en llegar |
| **v₀x** | ➡️ | Velocidad horizontal | Qué tan rápido va hacia adelante |
| **v₀y** | ⬆️ | Velocidad vertical | Qué tan rápido sube |
| **Δt** | 🕐 | Tiempo de reacción | Demora del defensor |

### 🎮 **En el Juego:**
- 💪 **Fuerza** = Variable **x** (compresión)
- 📐 **Ángulo** = Variable **θ** (dirección)
- 🤖 **El resto se calcula automáticamente** para garantizar la interceptación

### 💡 **Ejemplo Práctico:**
```
Si ajustas Fuerza = 0.8m y Ángulo = 45°:
v₀ = 0.8 × √(20000/10) = 0.8 × 44.7 = 35.8 m/s
¡El misil viaja a 35.8 metros por segundo!
```

### 🏭 **Parámetros del Sistema**

#### 🔴 **Misil Atacante (Rojo):**
- 🔧 **Rigidez resorte (k)**: 20,000 N/m 
- ⚖️ **Masa proyectil (m)**: 10 kg
- 💪 **Fuerza ajustable (x)**: 0.05-1.0 m
- 📐 **Ángulo ajustable (θ)**: 5°-85°

#### 🔵 **Misil Defensor (Azul):**
- 🔧 **Rigidez resorte (k)**: 25,000 N/m (¡más potente!)
- ⚖️ **Masa proyectil (m)**: 12 kg (más pesado pero más rígido)
- 🤖 **Control automático**: El sistema calcula todo
- ⚡ **Ventaja**: Mayor velocidad máxima disponible

#### 🌍 **Constantes Físicas:**
- **Gravedad (g)**: 9.81 m/s² (gravedad de la Tierra)
- **Precisión (ε)**: ±1.0 m (tolerancia de error)
- **Tiempo reacción**: 0-3 segundos

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
- **rich**: Animación en terminal

Todas las dependencias están especificadas en el archivo `requirements.txt` y pueden ser instaladas automáticamente usando el script `setup.py`.

## Configuración del entorno

El proyecto incluye un archivo `.env` que permite personalizar diferentes aspectos del simulador:

```
# Ejemplo de configuración en .env
GRAVITY=9.81            # Aceleración gravitacional
DEFAULT_DT=0.02         # Intervalo de tiempo para simulación
SHOW_ANIMATIONS=1       # Activar/desactivar animaciones
DEBUG=0                 # Modo debug
```

Puedes modificar estos valores según tus necesidades.

## 💡 Notas Importantes

### 🎨 **Advertencias Visuales**
- ⚠️ Las advertencias de emojis en matplotlib son normales y no afectan la funcionalidad
- 🖥️ El modo juego está optimizado para pantallas de 14" o mayores
- 🎯 La interceptación siempre es posible ajustando automáticamente los parámetros del defensor

### 🧠 **Consejos de Juego**
- 🎯 **45° es el ángulo mágico** para máximo alcance
- 💪 **Más fuerza** = trayectoria más larga y rápida
- 🎮 **Usa "Auto"** si no puedes interceptar manualmente
- 🖱️ **Haz click en el mapa** para posicionar rápidamente
- 📚 **Presiona "Ayuda"** para instrucciones detalladas

### 🔬 **Realismo Físico**
- ✅ Usa ecuaciones reales de balística
- ✅ Simula gravedad terrestre real
- ✅ Modelo de resortes basado en Ley de Hooke
- ✅ Conservación de energía aplicada correctamente

## 📊 **Ejemplos de Cálculos**

### 🧮 **Ejemplo 1: Misil Lento**
```
Configuración: Fuerza = 0.3m, Ángulo = 30°
Cálculo: v₀ = 0.3 × √(20000/10) = 0.3 × 44.7 = 13.4 m/s
Resultado: 🐌 Misil lento, alcance corto
```

### 🚀 **Ejemplo 2: Misil Rápido**
```
Configuración: Fuerza = 1.0m, Ángulo = 45°
Cálculo: v₀ = 1.0 × √(20000/10) = 1.0 × 44.7 = 44.7 m/s
Resultado: ⚡ Misil súper rápido, máximo alcance
```

### 🎯 **Ejemplo 3: Trayectoria Alta**
```
Configuración: Fuerza = 0.6m, Ángulo = 70°
Cálculo: v₀ = 0.6 × √(20000/10) = 0.6 × 44.7 = 26.8 m/s
Resultado: 🏔️ Vuela alto pero no muy lejos
```

## 🎮 **¡Empieza a Jugar!**

### 🚀 **Inicio Rápido:**
1. 📥 `python -m misiles.main --interactive`
2. 🎮 Selecciona opción **2** (Modo Juego)
3. 🖱️ Haz click en el mapa para posicionar el atacante
4. 🎚️ Ajusta **Fuerza** y **Ángulo**
5. 🛡️ ¡Presiona **¡Defender!** y observa la interceptación!

### 🏆 **Desafío:**
¿Puedes completar las 3 misiones sin usar el botón "Auto"? 
¡Conviértete en un experto en física de misiles! 🎯🚀
