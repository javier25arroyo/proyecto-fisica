"""Cálculo de v0 a partir de un resorte comprimido (Hooke + energía).
E_p = 1/2 k x^2 = 1/2 m v0^2 -> v0 = x * sqrt(k/m)
"""
from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Spring:
    k: float  # N/m
    x: float  # m (compresión)
    m: float  # kg

    def validate(self) -> None:
        if self.k <= 0 or self.x <= 0 or self.m <= 0:
            raise ValueError("k,x,m deben ser > 0")

    @property
    def v0(self) -> float:
        self.validate()
        return self.x * math.sqrt(self.k / self.m)

    @property
    def v0_max(self) -> float:
        # Para este modelo lineal, v0_max coincide con v0 dado x.
        return self.v0
