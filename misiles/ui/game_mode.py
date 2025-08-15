from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import math
from typing import Optional, Tuple, List

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider

from ..core.springs import Spring
from ..core.physics import deg2rad, rad2deg, position_at
from ..core.trajectories import generate_trajectory
from ..core.intercept import InterceptParams, solve_intercept_enumeration
from .params import load_scenario


@dataclass
class UIState:
    att_t: List[float]
    att_x: List[float]
    att_y: List[float]
    def_t: Optional[List[float]]
    def_x: Optional[List[float]]
    def_y: Optional[List[float]]
    impact: Optional[Tuple[float, float]]
    title: str


class GameApp:
    """
    Un "modo juego" para niños: controles grandes, textos simples y misiones.
    Presenta sólo lo esencial: mover atacante con el ratón, ajustar fuerza y ángulo,
    y pulsar "¡Defender!". Los números se reducen y se usan indicadores tipo videojuego.
    """

    def __init__(self):
        # Cargar escenario base
        scen_path = Path(__file__).resolve().parent.parent / 'scenarios' / 'baseline.json'
        with open(scen_path, 'r', encoding='utf-8') as f:
            self.scen = load_scenario(json.load(f))

        # Estado simple del atacante
        self.attacker = {
            'x0': self.scen.attacker.x0,
            'y0': max(0.0, self.scen.attacker.y0),
            'theta_deg': self.scen.attacker.theta_deg or 45.0,
            'spring_x': self.scen.attacker.spring.x,
            'mass': self.scen.attacker.spring.m,
        }

        # Figura grande estilo videojuego - tamaño mejorado
        self.fig, self.ax = plt.subplots(figsize=(14, 9))
        plt.subplots_adjust(left=0.08, right=0.92, top=0.88, bottom=0.20)
        self.ax.set_facecolor('#E6F4FF')  # cielo
        self.ax.grid(True, alpha=0.2)
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_xlabel('Distancia [metros]', fontsize=10)
        self.ax.set_ylabel('Altura [metros]', fontsize=10)

        # "Suelo"
        self.ax.axhline(0, color='#66BB6A', linewidth=6, alpha=0.8)

        # Curvas y marcadores
        (self.att_line,) = self.ax.plot([], [], '-', color='#E53935', linewidth=3, label='🚀 Rojo')
        (self.def_line,) = self.ax.plot([], [], '--', color='#1E88E5', linewidth=3, label='🛡️ Azul')
        (self.att_pt,) = self.ax.plot([], [], 'o', color='#E53935', markersize=10)
        (self.def_pt,) = self.ax.plot([], [], 'o', color='#1E88E5', markersize=10)

        # Lanzadores
        self.att_launch = self.ax.scatter([], [], marker='^', s=220, color='#B71C1C', zorder=10,
                                          edgecolors='white', linewidth=2, label='🔺 Atacante')
        self.def_base = self.ax.scatter([], [], marker='s', s=220, color='#0D47A1', zorder=10,
                                        edgecolors='white', linewidth=2, label='🟦 Defensor')
        # Intercepción
        self.impact_star = self.ax.scatter([], [], marker='*', s=300, color='gold', zorder=12,
                                           edgecolors='#B71C1C', linewidth=2, label='⭐ Interceptación')

        # HUD simple - mejor posicionado
        self.hud_text = self.ax.text(0.5, 0.94, '', transform=self.fig.transFigure, ha='center', va='center',
                                     fontsize=13, weight='bold', wrap=True)

        # Sliders GRANDES de "Fuerza" y "Ángulo" - mejor espaciados
        ax_power = self.fig.add_axes([0.08, 0.08, 0.38, 0.04])
        ax_angle = self.fig.add_axes([0.54, 0.08, 0.38, 0.04])
        self.s_power = Slider(ax_power, '💪 Fuerza', 0.05, 1.0, valinit=self.attacker['spring_x'])
        self.s_angle = Slider(ax_angle, '📐 Ángulo', 5.0, 85.0, valinit=self.attacker['theta_deg'])
        for s in (self.s_power, self.s_angle):
            s.label.set_fontsize(11)
            s.valtext.set_fontsize(10)

        # Botones grandes - mejor distribuidos y espaciados
        button_y = 0.91
        button_height = 0.05
        ax_play = self.fig.add_axes([0.08, button_y, 0.14, button_height])
        ax_reset = self.fig.add_axes([0.24, button_y, 0.14, button_height])
        ax_next = self.fig.add_axes([0.40, button_y, 0.18, button_height])
        ax_help = self.fig.add_axes([0.60, button_y, 0.12, button_height])
        ax_auto = self.fig.add_axes([0.74, button_y, 0.12, button_height])
        self.btn_play = Button(ax_play, '🛡️ ¡Defender!', color='#43A047', hovercolor='#2E7D32')
        self.btn_reset = Button(ax_reset, '🔄 Reiniciar', color='#8D6E63', hovercolor='#6D4C41')
        self.btn_next = Button(ax_next, '🎮 Siguiente misión', color='#3949AB', hovercolor='#283593')
        self.btn_help = Button(ax_help, '❓ Ayuda', color='#00ACC1', hovercolor='#00838F')
        self.btn_auto = Button(ax_auto, '✨ Auto', color='#FBC02D', hovercolor='#F9A825')
        
        # Ajustar tamaño de fuente de botones
        for btn in [self.btn_play, self.btn_reset, self.btn_next, self.btn_help, self.btn_auto]:
            btn.label.set_fontsize(9)

        # Misiones sencillas (preajustes) - textos más cortos
        self.missions = [
            {
                'name': 'Misión 1: ¡Detén el cohete rojo!',
                'hint': 'Clic en mapa para mover rojo. Ajusta Fuerza y Ángulo. ¡Defender!',
                'att': {'x0': -80.0, 'y0': 0.0, 'theta_deg': 45.0, 'spring_x': 0.45, 'mass': self.attacker['mass']},
                'def_x0': 0.0,
            },
            {
                'name': 'Misión 2: ¡Viene muy rápido!',
                'hint': 'Aumenta la Fuerza si no llegas a tiempo.',
                'att': {'x0': -120.0, 'y0': 0.0, 'theta_deg': 40.0, 'spring_x': 0.65, 'mass': self.attacker['mass']},
                'def_x0': 10.0,
            },
            {
                'name': 'Misión 3: ¡Apunta alto!',
                'hint': 'El rojo vuela alto. Prueba ángulos de 30°-60°.',
                'att': {'x0': -60.0, 'y0': 0.0, 'theta_deg': 55.0, 'spring_x': 0.55, 'mass': self.attacker['mass']},
                'def_x0': -10.0,
            },
        ]
        self.mission_index = 0

        # Estado de animación
        self.anim: Optional[FuncAnimation] = None

        # Posición inicial del defensor (slider interno camuflado) - mejor posicionado
        ax_hidden_defx0 = self.fig.add_axes([0.08, 0.01, 0.38, 0.02])
        ax_hidden_defx0.set_visible(False)
        self.s_defx0 = Slider(ax_hidden_defx0, '', -200.0, 200.0, valinit=self.scen.defender.x0)

        # Parámetros del sistema defensor simplificados (ocultos, pero con valores suaves)
        self.eps = self.scen.globals.eps
        self.delay_max = self.scen.globals.delay_max

        # Eventos
        self.fig.canvas.mpl_connect('button_press_event', self.on_click_place_attacker)
        self.btn_play.on_clicked(self.on_defend)
        self.btn_reset.on_clicked(self.on_reset)
        self.btn_next.on_clicked(self.on_next_mission)
        self.btn_help.on_clicked(self.on_help)
        self.btn_auto.on_clicked(self.on_auto)
        self.s_power.on_changed(self.on_change_controls)
        self.s_angle.on_changed(self.on_change_controls)

        # Primer arranque
        self.load_mission(self.mission_index)
        self.update_scene(self.compute())

    # Eventos UI
    def on_change_controls(self, _val):
        self.attacker['spring_x'] = float(self.s_power.val)
        self.attacker['theta_deg'] = float(self.s_angle.val)
        st = self.compute()
        self.update_scene(st)

    def on_click_place_attacker(self, event):
        if event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return
        # Colocar atacante donde haga clic (y no bajo el suelo)
        self.attacker['x0'] = float(event.xdata)
        self.attacker['y0'] = max(0.0, float(event.ydata))
        st = self.compute()
        self.update_scene(st)

    def on_defend(self, _):
        # Cálculo y animación. Si no hay intercepción, probamos ligeras ayudas.
        st = self.compute()
        if st.impact is None:
            # Ayuda suave: subir potencia defensiva y mover base un poco hacia el atacante
            self.s_defx0.set_val(self.attacker['x0'] + 30.0)
            st = self.compute(boost_defense=True)
        self.update_scene(st, animate=True)

    def on_reset(self, _):
        self.load_mission(self.mission_index)
        self.update_scene(self.compute())

    def on_next_mission(self, _):
        self.mission_index = (self.mission_index + 1) % len(self.missions)
        self.load_mission(self.mission_index)
        self.update_scene(self.compute())

    def on_help(self, _):
        print('\nAyuda rápida (Modo Juego):')
        print('1) Haz clic en el mapa para mover el cohete rojo (atacante).')
        print('2) Ajusta la Fuerza y el Ángulo con los deslizadores.')
        print('3) Pulsa "¡Defender!" para que el azul intercepte al rojo.')
        print('Consejo: si no llegas, prueba subir un poco la Fuerza. ¡Diviértete!')

    def on_auto(self, _):
        # Ajuste automático del defensor para favorecer intercepción
        st = self.compute(boost_defense=True)
        self.update_scene(st, animate=True)

    # Lógica
    def load_mission(self, idx: int):
        m = self.missions[idx]
        self.attacker.update(m['att'])
        self.s_power.set_val(self.attacker['spring_x'])
        self.s_angle.set_val(self.attacker['theta_deg'])
        self.s_defx0.set_val(m['def_x0'])
        # HUD
        self.hud_text.set_text(f"{m['name']}  |  💡 {m['hint']}")

    def compute(self, boost_defense: bool = False) -> UIState:
        g = self.scen.globals.g
        dt_sim = self.scen.globals.dt_sim
        dtheta = deg2rad(self.scen.globals.dtheta_deg)
        theta_min = deg2rad(5.0)
        theta_max = deg2rad(85.0)
        delay_min = 0.0
        delay_max = self.delay_max

        # Springs de atacante y defensor
        sp_a = self.scen.attacker.spring
        sp_d = self.scen.defender.spring
        att_sp = type(sp_a)(k=sp_a.k, x=self.attacker['spring_x'], m=self.attacker['mass'])
        def_x_val = sp_d.x if not boost_defense else min(1.0, sp_d.x * 1.15)
        def_sp = type(sp_d)(k=sp_d.k, x=def_x_val, m=sp_d.m)
        theta_a = deg2rad(self.attacker['theta_deg'])

        # Trayectoria atacante
        v0_a = Spring(k=att_sp.k, x=att_sp.x, m=att_sp.m).v0
        traj_a = generate_trajectory(self.attacker['x0'], self.attacker['y0'], v0_a, theta_a, dt_sim, g)

        # Solver del defensor
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
            eps=self.eps,
            g=g,
        )
        sol = solve_intercept_enumeration((traj_a.t, traj_a.x, traj_a.y), params, v0d_max)

        if not sol:
            title = 'Intenta ajustar Fuerza o Ángulo'
            return UIState(traj_a.t, traj_a.x, traj_a.y, None, None, None, None, title)

        # Trayectoria del defensor alineada con delay
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

        title = f"🎯 ¡Bien! Azul intercepta a Rojo"
        return UIState(traj_a.t, traj_a.x, traj_a.y, t_d_al, x_d_al, y_d_al, sol.impact_point, title)

    def update_scene(self, st: UIState, animate: bool = False):
        # Curvas
        self.att_line.set_data(st.att_x, st.att_y)
        if st.def_x is not None:
            self.def_line.set_data(st.def_x, st.def_y)
        else:
            self.def_line.set_data([], [])

        # Marcadores
        self.att_pt.set_data([], [])
        self.def_pt.set_data([], [])

        # Impacto
        if st.impact is not None:
            self.impact_star.set_offsets([st.impact])
        else:
            self.impact_star.set_offsets(np.empty((0, 2)))

        # Colocar lanzadores
        att_x0 = self.attacker['x0']
        att_y0 = self.attacker['y0']
        def_x0 = float(self.s_defx0.val)
        def_y0 = 0.0
        self.att_launch.set_offsets([[att_x0, att_y0]])
        self.def_base.set_offsets([[def_x0, def_y0]])

        # HUD texto - mejor ajustado
        self.fig.suptitle(st.title, fontsize=12, y=0.96)

        # Animación de puntos sobre las curvas
        if self.anim is not None and self.anim.event_source is not None:
            self.anim.event_source.stop()
            self.anim = None

        if animate:
            att_x, att_y = st.att_x, st.att_y
            def_x, def_y = st.def_x, st.def_y

            def update(frame):
                i_att = min(frame, len(att_x) - 1)
                self.att_pt.set_data([att_x[i_att]], [att_y[i_att]])
                if def_x is not None and def_y is not None and len(def_x) > 0:
                    i_def = min(frame, len(def_x) - 1)
                    self.def_pt.set_data([def_x[i_def]], [def_y[i_def]])
                return self.att_pt, self.def_pt

            frames = max(len(att_x), len(def_x) if def_x else len(att_x))
            self.anim = FuncAnimation(self.fig, update, frames=frames, interval=25, blit=True)

        # Escala automática
        self.ax.relim()
        self.ax.autoscale()
        self.fig.canvas.draw_idle()

    def run(self):
        # Mensaje de bienvenida sencillo en consola
        print('🎮 Modo Juego: Haz clic para mover el cohete rojo. Ajusta Fuerza y Ángulo. Pulsa ¡Defender!')
        plt.show()


def run_game():
    GameApp().run()
