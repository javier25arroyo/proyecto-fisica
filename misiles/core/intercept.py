"""Solvers de intercepción (enfoque A: barrido de punto de encuentro).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Tuple
import math

from .physics import position_at, GRAVITY_DEFAULT

@dataclass
class InterceptParams:
    # defensor fijo
    xd0: float
    yd0: float
    # rangos de búsqueda
    theta_min: float  # rad
    theta_max: float  # rad
    dtheta: float     # paso angular (rad)
    dt_attacker: float  # muestreo temporal atacante (s)
    dt_delay: float     # paso de retardo (s)
    delay_min: float
    delay_max: float
    eps: float = 1.0
    g: float = GRAVITY_DEFAULT

@dataclass
class InterceptSolution:
    theta_d: float
    delay: float
    v0_d: float
    impact_time: float  # tiempo del atacante en impacto
    impact_point: Tuple[float, float]
    error: float


def solve_intercept_enumeration(attacker_traj_txy: Tuple[list, list, list],
                                params: InterceptParams,
                                v0d_max: float) -> Optional[InterceptSolution]:
    """Barrido por candidato de tiempo del atacante, retardo y ángulo del defensor.

    attacker_traj_txy: (t_a, x_a, y_a) listas de igual longitud.
    v0d_max: velocidad máxima posible del defensor por su resorte.
    """
    t_a, x_a, y_a = attacker_traj_txy
    best: Optional[InterceptSolution] = None

    # precomputar ángulos
    thetas: List[float] = []
    th = params.theta_min
    while th <= params.theta_max + 1e-12:
        # evitar cos ~ 0
        if abs(math.cos(th)) > 1e-3:
            thetas.append(th)
        th += params.dtheta

    # retardo grid
    delays: List[float] = []
    d = params.delay_min
    while d <= params.delay_max + 1e-12:
        delays.append(d)
        d += params.dt_delay

    for ia in range(0, len(t_a)):
        ta = t_a[ia]
        Xa = x_a[ia]
        Ya = y_a[ia]
        if Ya < 0:
            continue
        for delay in delays:
            tau = ta - delay
            if tau <= 0:
                continue
            for th in thetas:
                # derivar v0d desde componente horizontal
                v0d = (Xa - params.xd0) / (tau * math.cos(th))
                if v0d <= 0 or not math.isfinite(v0d):
                    continue
                if v0d > v0d_max:
                    continue
                # comprobar vertical
                Ypred = params.yd0 + v0d * math.sin(th) * tau - 0.5 * params.g * tau * tau
                err = abs(Ya - Ypred)
                if err <= params.eps:
                    sol = InterceptSolution(theta_d=th, delay=delay, v0_d=v0d,
                                            impact_time=ta, impact_point=(Xa, Ya), error=err)
                    if best is None or sol.error < best.error or (
                        abs(sol.error - best.error) <= 1e-9 and sol.delay < best.delay
                    ):
                        best = sol
    return best
