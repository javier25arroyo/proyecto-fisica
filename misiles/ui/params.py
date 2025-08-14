"""Lectura y validación de parámetros desde JSON para escenarios."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class SpringSpec:
    k: float
    x: float
    m: float

@dataclass
class BodySpec:
    spring: SpringSpec
    theta_deg: float | None  # atacante debe traer theta; defensor None (se resuelve)
    x0: float
    y0: float

@dataclass
class Globals:
    g: float
    dt_sim: float
    eps: float
    theta_min_deg: float
    theta_max_deg: float
    dtheta_deg: float
    delay_min: float
    delay_max: float
    dt_delay: float

@dataclass
class Scenario:
    attacker: BodySpec
    defender: BodySpec
    globals: Globals


def load_scenario(data: Dict[str, Any]) -> Scenario:
    def sp(d: Dict[str, Any]) -> SpringSpec:
        return SpringSpec(k=float(d['k']), x=float(d['x']), m=float(d['m']))
    def body(d: Dict[str, Any]) -> BodySpec:
        return BodySpec(spring=sp(d['spring']),
                        theta_deg=(float(d['theta_deg']) if d.get('theta_deg') is not None else None),
                        x0=float(d['x0']), y0=float(d['y0']))
    g = data['globals']
    glob = Globals(g=float(g.get('g', 9.81)),
                   dt_sim=float(g.get('dt_sim', 0.01)),
                   eps=float(g.get('eps', 1.0)),
                   theta_min_deg=float(g.get('theta_min_deg', 5.0)),
                   theta_max_deg=float(g.get('theta_max_deg', 85.0)),
                   dtheta_deg=float(g.get('dtheta_deg', 0.5)),
                   delay_min=float(g.get('delay_min', 0.0)),
                   delay_max=float(g.get('delay_max', 5.0)),
                   dt_delay=float(g.get('dt_delay', 0.1)))
    return Scenario(attacker=body(data['attacker']),
                    defender=body(data['defender']),
                    globals=glob)
