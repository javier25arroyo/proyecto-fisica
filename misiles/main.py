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


def load_json(path: str | Path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    scen_path = Path(__file__).parent / 'scenarios' / 'baseline.json'
    data = load_json(scen_path)
    scen = load_scenario(data)

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
        plot_and_animate(
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

    plot_and_animate(
        attacker=TrajData(traj_a.t, traj_a.x, traj_a.y),
        defender=TrajData(t_d_aligned, x_d_aligned, y_d_aligned),
        impact=sol.impact_point,
        title=title,
    show=not is_agg,
    save_path=out_png,
    animate=not is_agg,
    )


if __name__ == '__main__':
    main()
