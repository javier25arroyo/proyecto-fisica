"""Visualización y animación con matplotlib."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
import math

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib

@dataclass
class TrajData:
    t: List[float]
    x: List[float]
    y: List[float]


def plot_and_animate(attacker: TrajData, defender: Optional[TrajData],
                     impact: Optional[Tuple[float, float]] = None,
                     title: str = "Intercepción 2D",
                     show: bool = True,
                     save_path: Optional[str] = None,
                     animate: bool = True):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')
    ax.grid(True)
    ax.set_aspect('equal', adjustable='box')

    ax.plot(attacker.x, attacker.y, '-', color='tab:blue', label='Atacante')
    if defender is not None:
        ax.plot(defender.x, defender.y, '--', color='tab:orange', label='Defensor')
    if impact is not None:
        ax.scatter([impact[0]], [impact[1]], color='red', zorder=5, label='Intersección')

    # animación opcional
    if animate:
        att_line, = ax.plot([], [], 'o', color='tab:blue')
        if defender is not None:
            def_line, = ax.plot([], [], 'o', color='tab:orange')
        else:
            def_line = None

        def init():
            att_line.set_data([], [])
            if def_line:
                def_line.set_data([], [])
            return (att_line,) if not def_line else (att_line, def_line)

        def update(frame):
            i_att = min(frame, len(attacker.t) - 1)
            att_line.set_data(attacker.x[i_att], attacker.y[i_att])
            if defender is not None and def_line is not None:
                i_def = min(frame, len(defender.t) - 1)
                def_line.set_data(defender.x[i_def], defender.y[i_def])
            return (att_line,) if not def_line else (att_line, def_line)

        frames = max(len(attacker.t), len(defender.t) if defender else len(attacker.t))
        _ani = FuncAnimation(fig, update, frames=frames, init_func=init, interval=20, blit=True)

    ax.legend()
    fig.suptitle(title)
    plt.tight_layout()
    non_interactive = matplotlib.get_backend().lower().startswith('agg')
    if save_path is not None:
        fig.savefig(save_path, dpi=120)
    if show and not non_interactive:
        plt.show()
    else:
        plt.close(fig)
