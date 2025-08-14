from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import math
from typing import Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button

from ..core.springs import Spring
from ..core.physics import deg2rad, rad2deg, position_at
from ..core.trajectories import generate_trajectory
from ..core.intercept import InterceptParams, solve_intercept_enumeration
from .params import load_scenario


@dataclass
class UIState:
    # arrays actuales para animación
    att_t: list
    att_x: list
    att_y: list
    def_t: Optional[list]
    def_x: Optional[list]
    def_y: Optional[list]
    impact: Optional[Tuple[float, float]]
    title: str


class InteractiveApp:
    def __init__(self):
        # cargar escenario por defecto
        scen_path = Path(__file__).resolve().parent.parent / 'scenarios' / 'baseline.json'
        with open(scen_path, 'r', encoding='utf-8') as f:
            self.scen = load_scenario(json.load(f))

        # figura y ejes
        self.fig, self.ax = plt.subplots(figsize=(9, 6))
        self.ax.set_xlabel('x [m]')
        self.ax.set_ylabel('y [m]')
        self.ax.grid(True)
        self.ax.set_aspect('equal', adjustable='box')
        plt.subplots_adjust(left=0.08, right=0.98, top=0.90, bottom=0.44)

        # líneas y marcadores
        (self.att_line,) = self.ax.plot([], [], '-', color='tab:blue', label='Atacante')
        (self.def_line,) = self.ax.plot([], [], '--', color='tab:orange', label='Defensor')
        (self.att_pt,) = self.ax.plot([], [], 'o', color='tab:blue')
        (self.def_pt,) = self.ax.plot([], [], 'o', color='tab:orange')
        self.impact_scatter = self.ax.scatter([], [], color='red', zorder=5, label='Intersección')
        self.ax.legend(loc='upper right')

        # sliders
        ax_ax0 = self.fig.add_axes([0.10, 0.34, 0.38, 0.03])
        ax_ay0 = self.fig.add_axes([0.52, 0.34, 0.38, 0.03])
        ax_theta = self.fig.add_axes([0.10, 0.29, 0.80, 0.03])
        ax_defx0 = self.fig.add_axes([0.10, 0.19, 0.80, 0.03])
        ax_eps = self.fig.add_axes([0.10, 0.14, 0.80, 0.03])
        ax_dly = self.fig.add_axes([0.10, 0.09, 0.80, 0.03])
        ax_attx = self.fig.add_axes([0.10, 0.04, 0.38, 0.03])
        ax_defx = self.fig.add_axes([0.52, 0.04, 0.38, 0.03])

        self.s_attx0 = Slider(ax_ax0, 'x0_att [m]', -500.0, 500.0, valinit=self.scen.attacker.x0)
        self.s_atty0 = Slider(ax_ay0, 'y0_att [m]', 0.0, 200.0, valinit=self.scen.attacker.y0)
        self.s_theta = Slider(ax_theta, 'θ_a [°]', 5.0, 85.0, valinit=self.scen.attacker.theta_deg or 45.0)
        self.s_defx0 = Slider(ax_defx0, 'x0_def [m]', -200.0, 200.0, valinit=self.scen.defender.x0)
        self.s_eps = Slider(ax_eps, 'ε [m]', 0.1, 5.0, valinit=self.scen.globals.eps)
        self.s_delay = Slider(ax_dly, 'Δt_max [s]', 0.0, 10.0, valinit=self.scen.globals.delay_max)
        self.s_attx = Slider(ax_attx, 'x_att [m]', 0.05, 1.0, valinit=self.scen.attacker.spring.x)
        self.s_defx = Slider(ax_defx, 'x_def [m]', 0.05, 1.0, valinit=self.scen.defender.spring.x)

        # botón resolver
        ax_btn = self.fig.add_axes([0.42, 0.915, 0.18, 0.05])
        self.btn = Button(ax_btn, 'Resolver y animar')

        # estado animación
        self.anim: Optional[FuncAnimation] = None
        self.state = UIState([], [], [], None, None, None, None, '')

        # eventos
        self.btn.on_clicked(self.on_resolve)
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.on_click)

        # primer render
        self.on_resolve(None)

    def compute(self) -> UIState:
        g = self.scen.globals.g
        dt_sim = self.scen.globals.dt_sim
        dtheta = deg2rad(self.scen.globals.dtheta_deg)
        theta_min = deg2rad(5.0)
        theta_max = deg2rad(85.0)
        delay_min = 0.0
        delay_max = float(self.s_delay.val)

        # Actualizar springs con x desde UI
        att_sp = self.scen.attacker.spring
        def_sp = self.scen.defender.spring
        att_sp = type(att_sp)(k=att_sp.k, x=float(self.s_attx.val), m=att_sp.m)
        def_sp = type(def_sp)(k=def_sp.k, x=float(self.s_defx.val), m=def_sp.m)
        theta_a = deg2rad(float(self.s_theta.val))

        # v0 atacante y trayectoria
        v0_a = Spring(k=att_sp.k, x=att_sp.x, m=att_sp.m).v0
        x0_att = float(self.s_attx0.val)
        y0_att = float(self.s_atty0.val)
        traj_a = generate_trajectory(x0_att, y0_att, v0_a, theta_a, dt_sim, g)

        # solver defensor
        v0d_max = Spring(k=def_sp.k, x=def_sp.x, m=def_sp.m).v0_max
        params = InterceptParams(
            xd0=float(self.s_defx0.val),
            yd0=self.scen.defender.y0,
            theta_min=theta_min,
            theta_max=theta_max,
            dtheta=dtheta,
            dt_attacker=dt_sim,
            dt_delay=self.scen.globals.dt_delay,
            delay_min=delay_min,
            delay_max=delay_max,
            eps=float(self.s_eps.val),
            g=g,
        )
        sol = solve_intercept_enumeration((traj_a.t, traj_a.x, traj_a.y), params, v0d_max)

        if not sol:
            title = f"Sin intercepción · v0_a={v0_a:.2f} m/s · v0_d,max={v0d_max:.2f} m/s"
            return UIState(traj_a.t, traj_a.x, traj_a.y, None, None, None, None, title)

        # trayectoria del defensor alineada con delay
        tau = sol.impact_time - sol.delay
        n = max(1, int(math.ceil(tau / dt_sim)))
        t_d = [i * dt_sim for i in range(n + 1)]
        x_d, y_d = [], []
        for t in t_d:
            xx, yy = position_at(t, params.xd0, params.yd0, sol.v0_d, sol.theta_d, g)
            x_d.append(xx)
            y_d.append(max(0.0, yy))
        ndelay = int(math.ceil(sol.delay / dt_sim))
        t_d_al = [i * dt_sim for i in range(ndelay + len(t_d))]
        x_d_al = [params.xd0] * ndelay + x_d
        y_d_al = [params.yd0] * ndelay + y_d

        title = (f"θ_d={rad2deg(sol.theta_d):.1f}°, Δt={sol.delay:.2f}s · "
                 f"v0_d={sol.v0_d:.2f} (max {v0d_max:.2f}) · v0_a={v0_a:.2f}")
        return UIState(traj_a.t, traj_a.x, traj_a.y, t_d_al, x_d_al, y_d_al, sol.impact_point, title)

    def on_click(self, event):
        # Fijar x0,y0 del atacante con click en el área del gráfico
        if event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return
        self.s_attx0.set_val(float(event.xdata))
        self.s_atty0.set_val(max(0.0, float(event.ydata)))
        self.on_resolve(None)

    def on_resolve(self, _):
        st = self.compute()

        # actualizar líneas
        self.att_line.set_data(st.att_x, st.att_y)
        if st.def_x is not None:
            self.def_line.set_data(st.def_x, st.def_y)
        else:
            self.def_line.set_data([], [])
        if st.impact is not None:
            self.impact_scatter.set_offsets([st.impact])
        else:
            self.impact_scatter.set_offsets([])
        self.fig.suptitle(st.title)

        # definir arrays para animación
        self._att_x = st.att_x
        self._att_y = st.att_y
        self._def_x = st.def_x
        self._def_y = st.def_y

        # reiniciar animación previa si existe
        if self.anim is not None and self.anim.event_source is not None:
            self.anim.event_source.stop()
            self.anim = None

        # crear nuevos marcadores animados sobre las curvas
        self.att_pt.set_data([], [])
        self.def_pt.set_data([], [])

        def update(frame):
            i_att = min(frame, len(self._att_x) - 1)
            self.att_pt.set_data([self._att_x[i_att]], [self._att_y[i_att]])
            if self._def_x is not None and self._def_y is not None and len(self._def_x) > 0:
                i_def = min(frame, len(self._def_x) - 1)
                self.def_pt.set_data([self._def_x[i_def]], [self._def_y[i_def]])
            else:
                self.def_pt.set_data([], [])
            return self.att_pt, self.def_pt

        frames = max(len(self._att_x), len(self._def_x) if self._def_x else len(self._att_x))
        self.anim = FuncAnimation(self.fig, update, frames=frames, interval=20, blit=True)

        # autoscale para abarcar todo
        self.ax.relim()
        self.ax.autoscale()
        self.fig.canvas.draw_idle()

    def run(self):
        plt.show()


def run():
    InteractiveApp().run()


if __name__ == '__main__':
    run()
