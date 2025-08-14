# Misiles – Simulación de intercepción 2D (sin rozamiento)

Proyecto educativo que calcula velocidades iniciales desde resortes (Ley de Hooke + conservación de energía), simula trayectorias balísticas y busca condiciones de disparo del defensor para interceptar a un atacante. Incluye animación con Matplotlib.

## Estructura

misiles/
- core/
  - physics.py – cinemática y utilidades (SI)
  - springs.py – v0 desde (k,x,m)
  - trajectories.py – generación de (t,x(t),y(t))
  - intercept.py – solver por barrido (enfoque A)
- ui/
  - params.py – carga/validación de escenarios JSON
  - viz_matplotlib.py – visualización y animación
- scenarios/
  - baseline.json – caso base
- main.py – orquestación (leer → resolver → animar)

## Requisitos

- Python 3.10+
- matplotlib

## Instalación rápida (Windows PowerShell)

```pwsh
py -3 -m venv .venv
. .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install matplotlib
```

## Ejecutar

```pwsh
python -m misiles.main
```

Si ejecutas desde la carpeta raíz del workspace y falla la importación, puedes correr:

```pwsh
python misiles/main.py
```

## Parámetros

Edita `misiles/scenarios/baseline.json`. Campos principales:
- attacker/defender.spring: {k, x, m}
- attacker.theta_deg: ángulo de ataque (grados)
- attacker/defender: x0, y0 posiciones iniciales
- globals: g, dt_sim, eps, theta_min_deg, theta_max_deg, dtheta_deg, delay_[min,max], dt_delay

## Notas

- Las unidades son SI.
- El solver descarta ángulos con cos(theta)≈0.
- Tolerancia espacial por defecto: 1 m.
- Reporta si no hay solución (por límite de resorte, geometría o retardo).
# Proyecto de física

