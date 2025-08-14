"""Física básica y utilidades matemáticas para misiles (SI units).
Determinista y testeable.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Iterable, Tuple

GRAVITY_DEFAULT = 9.81

@dataclass(frozen=True)
class LaunchState:
    x0: float
    y0: float
    v0: float
    theta: float  # radians


def flight_time(v0: float, theta: float, y0: float = 0.0, g: float = GRAVITY_DEFAULT) -> float:
    """Tiempo total de vuelo hasta y(t)=0 (>=0). Si y0>0 calcula raíz positiva.
    Si el proyectil no toca suelo (trayectoria siempre >0), retorna math.inf.
    """
    vy = v0 * math.sin(theta)
    disc = vy**2 + 2*g*y0
    if disc < 0:
        return math.inf
    t1 = (vy + math.sqrt(disc)) / g
    t2 = (vy - math.sqrt(disc)) / g
    # tiempo positivo mayor (impacto al suelo)
    candidates = [t for t in (t1, t2) if t > 0]
    return max(candidates) if candidates else 0.0


def range_flat_ground(v0: float, theta: float, y0: float = 0.0, g: float = GRAVITY_DEFAULT) -> float:
    """Alcance horizontal hasta y=0.
    Para y0=0 simplifica a v0^2 * sin(2*theta) / g.
    """
    tf = flight_time(v0, theta, y0, g)
    return v0 * math.cos(theta) * tf


def hmax(v0: float, theta: float, y0: float = 0.0, g: float = GRAVITY_DEFAULT) -> float:
    vy = v0 * math.sin(theta)
    return y0 + vy**2 / (2*g)


def position_at(t: float, x0: float, y0: float, v0: float, theta: float, g: float = GRAVITY_DEFAULT) -> Tuple[float, float]:
    vx = v0 * math.cos(theta)
    vy = v0 * math.sin(theta)
    x = x0 + vx * t
    y = y0 + vy * t - 0.5 * g * t * t
    return x, y


def clamp(v: float, vmin: float, vmax: float) -> float:
    return max(vmin, min(v, vmax))


def deg2rad(deg: float) -> float:
    return deg * math.pi / 180.0


def rad2deg(rad: float) -> float:
    return rad * 180.0 / math.pi
