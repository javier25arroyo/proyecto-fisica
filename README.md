# Simulación de Intercepción Balística 2D

Este proyecto simula un escenario de intercepción entre dos misiles en 2D, considerando:
- Lanzamiento por resorte (ley de Hooke + energía).
- Trayectorias balísticas sin rozamiento.
- Resolución visual animada.

## Estructura del proyecto

La estructura del proyecto está organizada de la siguiente manera:

```
misiles/                # Código fuente principal
├── core/               # Física, trayectorias, solver de intercepción
├── ui/                 # Visualización y UI interactiva
├── scenarios/          # Escenarios de ejemplo (JSON)
├── main.py             # Script principal para ejecutar la simulación
assets/videos/          # Videos de ejemplo de la simulación
```

## Requisitos

1. **Python 3.13+**
2. **Instalar dependencias:**
   ```bash
   pip install matplotlib
   ```

## Ejecución rápida

### 1. Simulación básica (headless, guarda imagen)
```bash
python -m misiles.main
```
- Genera `intercepcion.png` con la animación del escenario base.

### 2. Interfaz interactiva (sliders y click para origen)
```bash
python -m misiles.ui.interactive
```
- Permite ajustar parámetros y visualizar la animación en tiempo real.

### 3. Visualización enriquecida
- El script principal usa la animación rica por defecto.
- Para guardar imágenes en entornos sin GUI:
  ```bash
  set MPLBACKEND=Agg
  python -m misiles.main
  ```

## Video de ejemplo

Puedes ver una demostración directamente aquí:

<video controls width="600">
  <source src="assets/videos/intercepcion_demo.mp4" type="video/mp4">
  Tu navegador no soporta la reproducción de videos.
</video>

---

¡Listo para simular y visualizar trayectorias balísticas e interceptaciones!