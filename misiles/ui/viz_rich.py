from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import math

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle, Polygon, Rectangle

@dataclass
class TrajData:
    t: List[float]
    x: List[float]
    y: List[float]


def _heading(x: List[float], y: List[float], i: int) -> float:
    # ángulo de la velocidad (rad). Usa diferencias finitas.
    j0 = max(0, i - 1)
    j1 = min(len(x) - 1, i + 1)
    dx = x[j1] - x[j0]
    dy = y[j1] - y[j0]
    if dx == 0 and dy == 0:
        return 0.0
    return math.atan2(dy, dx)


def animate_rich(attacker: TrajData, defender: Optional[TrajData],
                 impact: Optional[Tuple[float, float]] = None,
                 title: str = "Intercepción 2D",
                 show: bool = True,
                 save_path: Optional[str] = None,
                 animate: bool = True):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')
    ax.grid(False)
    ax.set_aspect('equal', adjustable='box')

    # Fondo: cielo y suelo
    # Extensión aproximada en base a datos
    x_all = attacker.x + (defender.x if defender else [])
    y_all = attacker.y + (defender.y if defender else [])
    if not x_all:
        x_all = [0, 1]
    if not y_all:
        y_all = [0, 1]
    xmin, xmax = min(x_all), max(x_all)
    ymin, ymax = min(0.0, min(y_all)), max(y_all + [0.0])
    dx = xmax - xmin or 1.0
    dy = ymax - ymin or 1.0
    pad_x = 0.05 * dx
    pad_y = 0.10 * dy
    ax.set_xlim(xmin - pad_x, xmax + pad_x)
    ax.set_ylim(ymin - pad_y, ymax + pad_y)

    # Suelo
    ground = Rectangle((xmin - 10*dx, -1e6), width=100*dx, height=1e6, color='#6ab04c', alpha=0.5, zorder=0)
    ax.add_patch(ground)

    # Trayectorias “completadas hasta frame”
    att_path, = ax.plot([], [], color='tab:blue', linewidth=2.0, alpha=0.9, label='Atacante')
    def_path = None
    if defender is not None:
        def_path, = ax.plot([], [], color='tab:orange', linewidth=2.0, alpha=0.9, linestyle='--', label='Defensor')

    # Misiles: cuerpo (círculo) + llama (triángulo)
    att_body = Circle((0, 0), radius=0.8*max(dx, dy)/100.0, color='#1f77b4', zorder=5)
    ax.add_patch(att_body)
    att_flame = Polygon([[0,0]], closed=True, color='#f39c12', alpha=0.8, zorder=4)
    ax.add_patch(att_flame)

    def_body = None
    def_flame = None
    if defender is not None:
        def_body = Circle((0, 0), radius=0.8*max(dx, dy)/100.0, color='#e67e22', zorder=5)
        def_flame = Polygon([[0,0]], closed=True, color='#f1c40f', alpha=0.8, zorder=4)
        ax.add_patch(def_body)
        ax.add_patch(def_flame)

    # Intersección: explosión (círculo expansivo)
    explosion = None
    exp_frame = None
    if impact is not None:
        # localizar frame más cercano del atacante al punto de impacto
        import numpy as np
        ax.scatter([impact[0]], [impact[1]], s=30, color='red', zorder=6)  # marcador pequeño permanente
        dists = np.hypot(np.array(attacker.x) - impact[0], np.array(attacker.y) - impact[1])
        exp_frame = int(np.argmin(dists))
        explosion = Circle((impact[0], impact[1]), radius=0.1, fill=False,
                           edgecolor='#f1c40f', linewidth=3, alpha=0.0, zorder=6)
        ax.add_patch(explosion)

    # Leyenda y título
    ax.legend(loc='upper right')
    fig.suptitle(title)
    plt.tight_layout()

    if not animate:
        # Dibujo estático (trayectoria completa)
        att_path.set_data(attacker.x, attacker.y)
        if defender is not None and def_path is not None:
            def_path.set_data(defender.x, defender.y)
        if save_path:
            fig.savefig(save_path, dpi=140)
        if show and not matplotlib.get_backend().lower().startswith('agg'):
            plt.show()
        else:
            plt.close(fig)
        return

    frames = max(len(attacker.t), len(defender.t) if defender else len(attacker.t))

    def missile_shape(xc: float, yc: float, heading: float, scale: float = 1.0):
        # llama como triángulo detrás del cuerpo
        L = 4.0 * scale * max(dx, dy)/100.0
        W = 2.0 * scale * max(dx, dy)/100.0
        # vector dirección
        ux = math.cos(heading)
        uy = math.sin(heading)
        # punto detrás del cuerpo
        back_x = xc - ux * 1.2 * L
        back_y = yc - uy * 1.2 * L
        left_x = back_x + (-uy) * W
        left_y = back_y + (ux) * W
        right_x = back_x - (-uy) * W
        right_y = back_y - (ux) * W
        tip_x = xc - ux * 0.6 * L
        tip_y = yc - uy * 0.6 * L
        return [(left_x, left_y), (right_x, right_y), (tip_x, tip_y)]

    def update(i: int):
        i_att = min(i, len(attacker.x) - 1)
        att_path.set_data(attacker.x[:i_att+1], attacker.y[:i_att+1])
        ha = _heading(attacker.x, attacker.y, i_att)
        att_body.center = (attacker.x[i_att], attacker.y[i_att])
        att_flame.set_xy(missile_shape(attacker.x[i_att], attacker.y[i_att], ha, 1.0))

        if defender is not None and def_path is not None:
            i_def = min(i, len(defender.x) - 1)
            def_path.set_data(defender.x[:i_def+1], defender.y[:i_def+1])
            if def_body is not None and def_flame is not None and i_def >= 0:
                hd = _heading(defender.x, defender.y, i_def)
                def_body.center = (defender.x[i_def], defender.y[i_def])
                def_flame.set_xy(missile_shape(defender.x[i_def], defender.y[i_def], hd, 1.0))

        # explosión: crecer y desvanecer durante ~40 frames
        if explosion is not None and exp_frame is not None:
            span = 40
            k = i - exp_frame
            if 0 <= k < span:
                r = (k + 1) / span * (0.06 * (dx + dy))
                explosion.set_alpha(max(0.0, 1.0 - k/span))
                explosion.set_radius(r)
            elif k >= span:
                explosion.set_alpha(0.0)

        return []

    ani = FuncAnimation(fig, update, frames=frames, interval=20, blit=False)

    non_interactive = matplotlib.get_backend().lower().startswith('agg')
    if save_path is not None:
        # Intentar guardar como PNG si extensión es .png, o como mp4 si .mp4 y hay writer
        try:
            if save_path.lower().endswith('.mp4'):
                ani.save(save_path, writer='ffmpeg', fps=50)
            else:
                fig.savefig(save_path, dpi=140)
        except Exception:
            # Fallback silencioso
            fig.savefig(save_path if save_path.lower().endswith('.png') else save_path + '.png', dpi=140)
    if show and not non_interactive:
        plt.show()
    else:
        plt.close(fig)
