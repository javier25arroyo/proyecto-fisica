"""Generación de trayectorias paramétricas sin rozamiento."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import math

from .physics import position_at, flight_time, GRAVITY_DEFAULT

@dataclass
class Trajectory:
    t: List[float]
    x: List[float]
    y: List[float]


def generate_trajectory(x0: float, y0: float, v0: float, theta: float, dt: float,
                        g: float = GRAVITY_DEFAULT, t_max: float | None = None) -> Trajectory:
    if dt <= 0:
        raise ValueError("dt debe ser > 0")
    tf = flight_time(v0, theta, y0, g)
    if t_max is not None:
        tf = min(tf, t_max)
    n = max(1, int(math.ceil(tf / dt)))
    t_list: List[float] = []
    x_list: List[float] = []
    y_list: List[float] = []
    for i in range(n + 1):
        t = i * dt
        xx, yy = position_at(t, x0, y0, v0, theta, g)
        if yy < 0:
            # cortar exactamente al suelo (interpolar linealmente en el último tramo)
            if i > 0:
                t_prev = (i - 1) * dt
                x_prev, y_prev = position_at(t_prev, x0, y0, v0, theta, g)
                # interpolación lineal para y=0
                alpha = (0 - y_prev) / (yy - y_prev)
                t0 = t_prev + alpha * dt
                x0i = x_prev + alpha * (xx - x_prev)
                t_list.append(t0)
                x_list.append(x0i)
                y_list.append(0.0)
            break
        t_list.append(t)
        x_list.append(xx)
        y_list.append(yy)
    return Trajectory(t_list, x_list, y_list)
