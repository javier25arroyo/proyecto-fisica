from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path
import math

from .core.physics import deg2rad, rad2deg, GRAVITY_DEFAULT
from .core.springs import Spring
from .core.trajectories import generate_trajectory, Trajectory
from .core.intercept import InterceptParams, solve_intercept_enumeration
from .ui.params import load_scenario
from .ui.viz_matplotlib import plot_and_animate, TrajData
from .ui.viz_matplotlib import plot_and_animate as plot_basic, TrajData
from .ui.viz_rich import animate_rich
from .ui.interactive import interactive_attacker_setup, run_enhanced


def load_json(path: str | Path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main_with_params(attacker_params=None):
    scen_path = Path(__file__).parent / 'scenarios' / 'baseline.json'
    data = load_json(scen_path)
    scen = load_scenario(data)
    
    # Aplicar parámetros personalizados del atacante si se proporcionan
    if attacker_params:
        scen.attacker.x0 = attacker_params.get('x0', scen.attacker.x0)
        scen.attacker.y0 = attacker_params.get('y0', scen.attacker.y0)
        scen.attacker.theta_deg = attacker_params.get('theta_deg', scen.attacker.theta_deg)
        
        # Actualizar parámetros del resorte
        if 'spring_x' in attacker_params:
            scen.attacker.spring.x = attacker_params['spring_x']
        if 'mass' in attacker_params:
            scen.attacker.spring.m = attacker_params['mass']

    # atacante
    sp_a = scen.attacker.spring
    spring_a = Spring(k=sp_a.k, x=sp_a.x, m=sp_a.m)
    v0_a = spring_a.v0
    if v0_a <= 0:
        raise SystemExit('Atacante no despega: v0_a<=0')
    theta_a = deg2rad(scen.attacker.theta_deg or 45.0)

    # trayectoria atacante
    traj_a = generate_trajectory(scen.attacker.x0, scen.attacker.y0, v0_a, theta_a,
                                 dt=scen.globals.dt_sim, g=scen.globals.g)

    # solver intercepción
    sp_d = scen.defender.spring
    spring_d = Spring(k=sp_d.k, x=sp_d.x, m=sp_d.m)
    v0d_max = spring_d.v0_max

    params = InterceptParams(
        xd0=scen.defender.x0,
        yd0=scen.defender.y0,
        theta_min=deg2rad(scen.globals.theta_min_deg),
        theta_max=deg2rad(scen.globals.theta_max_deg),
        dtheta=deg2rad(scen.globals.dtheta_deg),
        dt_attacker=scen.globals.dt_sim,
        dt_delay=scen.globals.dt_delay,
        delay_min=scen.globals.delay_min,
        delay_max=scen.globals.delay_max,
        eps=scen.globals.eps,
        g=scen.globals.g,
    )

    sol = solve_intercept_enumeration((traj_a.t, traj_a.x, traj_a.y), params, v0d_max)

    if not sol:
        print('No hay solución de intercepción con los parámetros dados.')
        print(f"v0_a={v0_a:.3f} m/s; v0_d,max={v0d_max:.3f} m/s")
        import matplotlib
        is_agg = matplotlib.get_backend().lower().startswith('agg')
        out_png = None
        if is_agg:
            out_png = str(Path(__file__).parent / 'sin_intercepcion.png')
        # Visualización rica también para el caso sin solución
        animate_rich(
            TrajData(traj_a.t, traj_a.x, traj_a.y),
            None,
            None,
            title='Sin intercepción posible',
            show=not is_agg,
            save_path=out_png,
            animate=not is_agg,
        )
        return

    # generar trayectoria del defensor con la solución hallada
    # su tiempo propio arranca en t=0 cuando dispara, pero para animación
    # alineamos con el tiempo del atacante: añadimos delay con puntos planos al inicio
    theta_d = sol.theta_d
    v0_d = sol.v0_d

    # Construimos la trayectoria del defensor en su propio tiempo (0..tau)
    tau = sol.impact_time - sol.delay
    dt = scen.globals.dt_sim
    n = max(1, int(math.ceil(tau/dt)))
    t_d = [i*dt for i in range(n+1)]
    from .core.physics import position_at
    x_d = []
    y_d = []
    for t in t_d:
        xx, yy = position_at(t, scen.defender.x0, scen.defender.y0, v0_d, theta_d, scen.globals.g)
        x_d.append(xx)
        y_d.append(max(0.0, yy))

    # insertar delay (mantener estático hasta disparo)
    ndelay = int(math.ceil(sol.delay / dt))
    t_d_aligned = [i*dt for i in range(ndelay + len(t_d))]
    x_d_aligned = [scen.defender.x0]*ndelay + x_d
    y_d_aligned = [scen.defender.y0]*ndelay + y_d

    # UI: texto de HUD como título
    title = (f"Intercepción: θ_d={rad2deg(theta_d):.2f}°, Δt={sol.delay:.2f}s, "
             f"v0_a={v0_a:.2f} m/s, v0_d={v0_d:.2f} m/s (max {v0d_max:.2f})")

    # Guardado opcional en modo headless
    import matplotlib
    is_agg = matplotlib.get_backend().lower().startswith('agg')
    out_png = None
    if is_agg:
        out_png = str(Path(__file__).parent / 'intercepcion.png')

    animate_rich(
        attacker=TrajData(traj_a.t, traj_a.x, traj_a.y),
        defender=TrajData(t_d_aligned, x_d_aligned, y_d_aligned),
        impact=sol.impact_point,
        title=title,
        show=not is_agg,
        save_path=out_png,
        animate=not is_agg,
    )


def main():
    """Función principal por defecto (usa parámetros del baseline.json)"""
    main_with_params()


def main_interactive():
    """Función principal con entrada interactiva de parámetros del atacante"""
    print("¡Bienvenido al simulador de misiles!")
    print("\nOpciones disponibles:")
    print("1. Usar configuración por defecto")
    print("2. Configurar parámetros del atacante por consola")
    print("3. Interfaz gráfica completa (RECOMENDADO)")
    
    while True:
        try:
            choice = input("\nSeleccione una opción (1, 2 o 3): ").strip()
            if choice == '1':
                print("\nUsando configuración por defecto...")
                main_with_params()
                break
            elif choice == '2':
                print("\nConfiguración interactiva por consola...")
                attacker_params = interactive_attacker_setup()
                print("\n¡Iniciando simulación con parámetros personalizados!")
                main_with_params(attacker_params)
                break
            elif choice == '3':
                print("\n🚀 Iniciando interfaz gráfica mejorada...")
                run_enhanced()
                break
            else:
                print("Error: Seleccione 1, 2 o 3")
        except KeyboardInterrupt:
            print("\n\nSimulación cancelada por el usuario.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            break


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        main_interactive()
    else:
        main()
