from __future__ import annotations
import math
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import FancyArrowPatch

from .core.springs import Spring
from .core.physics import position_at, rad2deg
from .core.trajectories import generate_trajectory
from .ui.params import load_scenario
from .ui.viz_rich import TrajData

# === Parámetros de la simulación controlada ===
REACTION_TIME = 1.5                 # tiempo mínimo de reacción del defensor (s)
MAX_DEFENDER_COMPRESSION = 1.5       # compresión máxima permitida (m)
ATTACKER_MASS = 1.5                 # masa fija del atacante (kg)
DEFENDER_MASS = 1.0       


def load_json(path: str | Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- utilidades físicas ----------
def suggest_distance(attacker_k: float, x: float, theta_deg: float, m: float, g: float) -> tuple[float, float]:
    theta_rad = math.radians(theta_deg)
    R_est = (attacker_k * x**2) / (m * g) * math.sin(2.0 * theta_rad)
    return max(0.0, R_est - 25.0), R_est

def compute_intercept(scen, x: float, theta_deg: float, side_att: str, dist_att: float,
                      side_def: str, dist_def: float):
    """
    Devuelve dict con:
      - attacker: TrajData(t, x, y)
      - defender: TrajData(t, x, y)
      - impact: (x, y)
      - impact_idx_att: índice del atacante en el impacto
      - impact_idx_def: índice del defensor en el impacto (último)
      - title, info
    Lanza ValueError con mensaje si no hay intercepción posible.
    """
    # Posiciones relativas a x=0
    x0_att = -dist_att if side_att == "izquierda" else dist_att
    x0_def = -dist_def if side_def == "izquierda" else dist_def

    # Configurar escenario
    scen.attacker.spring.x = x
    scen.attacker.spring.m = ATTACKER_MASS
    scen.attacker.theta_deg = theta_deg
    scen.attacker.x0 = x0_att

    scen.defender.x0 = x0_def
    scen.defender.spring.m = DEFENDER_MASS
    scen.defender.spring.k = scen.attacker.spring.k  # igualamos hardware

    # Trayectoria atacante
    spring_a = Spring(k=scen.attacker.spring.k, x=x, m=ATTACKER_MASS)
    v0_a = spring_a.v0
    theta_a = math.radians(theta_deg)
    traj_a = generate_trajectory(x0_att, scen.attacker.y0, v0_a, theta_a,
                                 dt=scen.globals.dt_sim, g=scen.globals.g)

    # Vel máx del defensor (para info)
    k_d = scen.defender.spring.k
    m_d = scen.defender.spring.m
    v0_d_max = MAX_DEFENDER_COMPRESSION * math.sqrt(k_d / m_d)

    # Aterrizaje atacante (cruce y=0)
    x_land, t_land = traj_a.x[-1], traj_a.t[-1]
    for i in range(1, len(traj_a.t)):
        if traj_a.y[i-1] > 0 and traj_a.y[i] <= 0:
            y1, y2 = traj_a.y[i-1], traj_a.y[i]
            x1, x2 = traj_a.x[i-1], traj_a.x[i]
            t1, t2 = traj_a.t[i-1], traj_a.t[i]
            denom = (y2 - y1) if (y2 - y1) != 0 else 1e-12
            alpha = (0 - y1) / denom
            x_land = x1 + alpha * (x2 - x1)
            t_land = t1 + alpha * (t2 - t1)
            break

    # Punto ideal: ±25 m
    x_target_ideal = -25.0 if x0_att < 0 else 25.0
    reaches = (x0_att < 0 and x_land >= x_target_ideal) or (x0_att > 0 and x_land <= x_target_ideal)
    if not reaches:
        raise ValueError(
            f"El atacante no alcanza la zona objetivo de intercepción.\n"
            f"Aterriza en x ≈ {x_land:.1f} m (t ≈ {t_land:.2f} s); objetivo en x = {x_target_ideal:.1f} m.\n"
            f"Sugerencias: más compresión, ángulo 35°–55° o acercar atacante."
        )

    # Tiempo en que pasa por el objetivo ideal
    t_at_target, idx_at_target = None, None
    for i, (t_val, x_val) in enumerate(zip(traj_a.t, traj_a.x)):
        if x0_att < 0 and x_val >= x_target_ideal:
            t_at_target, idx_at_target = t_val, i
            break
        if x0_att > 0 and x_val <= x_target_ideal:
            t_at_target, idx_at_target = t_val, i
            break
    if t_at_target is None:
        raise ValueError("El atacante no pasa por el punto objetivo durante la simulación numérica.")

    def compression_required_to_hit(x_t, y_t, t_t):
        dx = x_t - x0_def
        dy = y_t - scen.defender.y0
        t  = REACTION_TIME
        v0x = dx / t
        v0y = (dy + 0.5 * scen.globals.g * t**2) / t
        v0_needed = math.hypot(v0x, v0y)
        x_req = math.sqrt((m_d * v0_needed**2) / k_d)
        theta_d = math.atan2(v0y, v0x)
        return x_req, v0_needed, theta_d

    # Intentar punto ideal
    y_at_target = max(0.0, traj_a.y[idx_at_target])
    x_req, v0_need, theta_d = compression_required_to_hit(x_target_ideal, y_at_target, t_at_target)

    if t_at_target > REACTION_TIME and x_req <= MAX_DEFENDER_COMPRESSION:
        chosen = dict(x=x_target_ideal, y=y_at_target, t=t_at_target, x_req=x_req, v0_need=v0_need, theta_d=theta_d)
    else:
        # Fallback: mejor punto factible antes del objetivo
        best = None
        def before_ideal(i):
            if x0_att < 0:
                return traj_a.x[i] <= x_target_ideal
            else:
                return traj_a.x[i] >= x_target_ideal

        for i, (t_val, x_val, y_val) in enumerate(zip(traj_a.t, traj_a.x, traj_a.y)):
            if t_val < REACTION_TIME:
                continue
            if not before_ideal(i):
                break
            x_curr, y_curr = x_val, max(0.0, y_val)
            x_req_i, v0_need_i, theta_d_i = compression_required_to_hit(x_curr, y_curr, t_val)
            if x_req_i <= MAX_DEFENDER_COMPRESSION:
                if best is None or x_req_i < best["x_req"]:
                    best = dict(x=x_curr, y=y_curr, t=t_val, x_req=x_req_i, v0_need=v0_need_i, theta_d=theta_d_i)

        if best is None:
            raise ValueError(
                "No es posible interceptar con las capacidades actuales del defensor.\n"
                f"La velocidad inicial del defensor es ≈ {MAX_DEFENDER_COMPRESSION * math.sqrt(k_d/m_d):.2f} m/s "
                f"(k={k_d}, m={m_d}, x_max={MAX_DEFENDER_COMPRESSION})\n"
                f"En el punto ideal de intercepcion (±25 m): La velocidad inicial requerida para el defensor es de ≈ {v0_need:.2f} m/s, compresión ≈ {x_req:.2f} m\n"
                "Opciones: acercar defensor, reducir el tiempo de reaccion, aumentar compresión máx o k del resorte del defensor."
            )
        chosen = best

    # Trazo del defensor
    t_launch_def = chosen["t"] - REACTION_TIME
    theta_d = chosen["theta_d"]
    x_required = chosen["x_req"]

    spring_d = Spring(k=k_d, x=x_required, m=m_d)
    v0_d = spring_d.v0

    dt = scen.globals.dt_sim
    n = max(1, int(REACTION_TIME / dt))
    t_d = [i * dt for i in range(n + 1)]
    x_d, y_d = [], []
    for tt in t_d:
        xx, yy = position_at(tt, x0_def, scen.defender.y0, v0_d, theta_d, scen.globals.g)
        x_d.append(xx)
        y_d.append(max(0.0, yy))

    # Alinear con delay
    ndelay = int(math.ceil(t_launch_def / dt))
    t_def_full = [i * dt for i in range(ndelay + len(t_d))]
    x_def_full = [x0_def] * ndelay + x_d
    y_def_full = [scen.defender.y0] * ndelay + y_d

    # Índices de impacto para cortar animación
    # Atacante: índice donde t >= chosen['t']
    impact_idx_att = next((i for i, t in enumerate(traj_a.t) if t >= chosen["t"]), len(traj_a.t)-1)
    # Defensor: llega al final de su serie alineada
    impact_idx_def = len(t_def_full) - 1

    title = (
        f"Intercepción a =  {chosen['x']:.1f} m del objetivo, y ≈ {chosen['y']:.1f} m de altura\n"
        f"Angulo inicial = {rad2deg(theta_d):.2f}°, compresión requerida del defensor = {x_required:.2f} m, "
        f"lanzamiento a  = {t_launch_def:.2f} s después del atacante\n"
    )

    return dict(
        attacker=TrajData(traj_a.t, traj_a.x, traj_a.y),
        defender=TrajData(t_def_full, x_def_full, y_def_full),
        impact=(chosen["x"], chosen["y"]),
        impact_idx_att=impact_idx_att,
        impact_idx_def=impact_idx_def,
        title=title,
        info=f"v0_atacante ≈ {v0_a:.2f} m/s; v0_defensor,max ≈ {MAX_DEFENDER_COMPRESSION * math.sqrt(k_d/m_d):.2f} m/s"
    )

# ----------------------- GUI -----------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador de Intercepción de Misiles")
        self.geometry("900x650")

        scen_path = Path(__file__).parent / "scenarios" / "baseline.json"
        self.scen = load_scenario(load_json(scen_path))

        # Variables de entrada
        self.var_x = tk.DoubleVar(value=0.6)
        self.var_theta = tk.DoubleVar(value=45.0)
        self.var_side_att = tk.StringVar(value="izquierda")
        self.var_dist_att = tk.DoubleVar(value=300.0)
        self.var_side_def = tk.StringVar(value="derecha")
        self.var_dist_def = tk.DoubleVar(value=100.0)

        frm = ttk.LabelFrame(self, text="Parámetros")
        frm.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        def row(r, label, widget):
            ttk.Label(frm, text=label).grid(row=r, column=0, sticky="w", padx=5, pady=4)
            widget.grid(row=r, column=1, sticky="we", padx=5, pady=4)

        row(0, "Compresión del resorte atacante x [m] (0.3–1.0):", ttk.Entry(frm, textvariable=self.var_x))
        row(1, "Ángulo atacante θ [°] (10–80):", ttk.Entry(frm, textvariable=self.var_theta))
        att_side = ttk.Combobox(frm, values=["izquierda", "derecha"], textvariable=self.var_side_att, state="readonly")
        def_side = ttk.Combobox(frm, values=["izquierda", "derecha"], textvariable=self.var_side_def, state="readonly")
        row(2, "Lado del atacante:", att_side)
        row(3, "Distancia del atacante con el objetivo [m] (0–700):", ttk.Entry(frm, textvariable=self.var_dist_att))
        row(4, "Lado del defensor:", def_side)
        row(5, "Distancia defensor con el objetivo [m] (0–200):", ttk.Entry(frm, textvariable=self.var_dist_def))

        self.lbl_suggestion = ttk.Label(frm, text="", foreground="")
        self.lbl_suggestion.grid(row=6, column=0, columnspan=2, sticky="w", padx=5, pady=4)

        # Botones
        btns = ttk.Frame(self)
        btns.pack(side=tk.TOP, fill=tk.X, padx=10)
        ttk.Button(btns, text="Sugerir distancia atacante", command=self.on_suggest).pack(side=tk.LEFT, padx=5, pady=8)
        ttk.Button(btns, text="Iniciar", command=self.on_start).pack(side=tk.LEFT, padx=5, pady=8)
        self.btn_pause = ttk.Button(btns, text="Pausar", command=self.on_pause)
        self.btn_pause.pack(side=tk.LEFT, padx=5, pady=8)
        ttk.Button(btns, text="Reset", command=self.on_reset).pack(side=tk.LEFT, padx=5, pady=8)

        # Figure
        self.fig = Figure(figsize=(7.2, 4.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("x [m]")
        self.ax.set_ylabel("y [m]")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Estado animación
        self.anim_running = False
        self.anim_paused = False
        self.anim_idx = 0
        self.A = None
        self.D = None
        self.impact = None
        self.impact_idx_att = None
        self.impact_idx_def = None

        # Elementos gráficos
        self.line_att, = self.ax.plot([], [], lw=2.0, label="Atacante", color="tab:orange")
        self.line_def, = self.ax.plot([], [], lw=2.0, label="Defensor", color="tab:blue")
        self.pt_impact = self.ax.plot([], [], marker="o", markersize=8, color="tab:red")[0]
        self.quiver_att = None
        self.quiver_def = None
        self.ax.legend(loc="best")

    # --------- UI handlers ----------
    def on_suggest(self):
        try:
            x = float(self.var_x.get()); theta = float(self.var_theta.get())
            if not (0.3 <= x <= 1.0 and 10 <= theta <= 80):
                raise ValueError("Rangos: x[0.3–1.0], θ[10–80]")
            k = self.scen.attacker.spring.k; g = self.scen.globals.g
            suggested_max, R_est = suggest_distance(k, x, theta, ATTACKER_MASS, g)
            self.lbl_suggestion.config(
                text=(f"Sugerencia: con x={x:.2f} m, θ={theta:.1f}°, alcance≈{R_est:.1f} m → "
                      f"distancia atacante ≤ {suggested_max:.1f} m para cruzar el punto de intercepción."),
                foreground="blue"
            )
        except Exception as e:
            self.lbl_suggestion.config(text=f"Error de sugerencia: {e}", foreground="red")

    def on_start(self):
        if self.anim_running:
            return
        try:
            x = float(self.var_x.get())
            theta = float(self.var_theta.get())
            side_att = self.var_side_att.get()
            dist_att = float(self.var_dist_att.get())
            side_def = self.var_side_def.get()
            dist_def = float(self.var_dist_def.get())

            if not (0.3 <= x <= 1.0): raise ValueError("x fuera de rango [0.3–1.0]")
            if not (10 <= theta <= 80): raise ValueError("θ fuera de rango [10–80]")
            if not (0 <= dist_att <= 700): raise ValueError("distancia atacante fuera de rango [0–700]")
            if not (0 <= dist_def <= 200): raise ValueError("distancia defensor fuera de rango [0–200]")

            res = compute_intercept(self.scen, x, theta, side_att, dist_att, side_def, dist_def)
            self.A, self.D = res["attacker"], res["defender"]
            self.impact = res["impact"]
            self.impact_idx_att = res["impact_idx_att"]
            self.impact_idx_def = res["impact_idx_def"]
            title = res["title"]

            # Preparar ejes
            self.ax.clear()
            self.ax.set_xlabel("x [m]"); self.ax.set_ylabel("y [m]")
            # Límites hasta el impacto (para enfocarlo)
            all_x = list(self.A.x[:self.impact_idx_att+1]) + list(self.D.x[:self.impact_idx_def+1])
            all_y = list(self.A.y[:self.impact_idx_att+1]) + list(self.D.y[:self.impact_idx_def+1])
            ymax = max(1.0, max(all_y) * 1.1)
            xmin = min(all_x) - 10.0; xmax = max(all_x) + 10.0
            self.ax.set_xlim(xmin, xmax); self.ax.set_ylim(0, ymax)
            self.ax.set_title(title)

            # Líneas y marcador
            self.line_att, = self.ax.plot([], [], lw=2.0, label="Atacante", color="tab:orange")
            self.line_def, = self.ax.plot([], [], lw=2.0, label="Defensor", color="tab:blue")
            self.pt_impact = self.ax.plot([], [], marker="o", markersize=8, color="tab:red")[0]

            # Flechas (FancyArrowPatch) — se actualizan en cada frame
            self.quiver_att = FancyArrowPatch((0,0), (0,0), arrowstyle='->', mutation_scale=12, color="tab:orange")
            self.quiver_def = FancyArrowPatch((0,0), (0,0), arrowstyle='->', mutation_scale=12, color="tab:blue")
            self.ax.add_patch(self.quiver_att)
            self.ax.add_patch(self.quiver_def)

            self.ax.legend(loc="best")
            self.canvas.draw()

            # Animación
            self.anim_idx = 0
            self.anim_running = True
            self.anim_paused = False
            self.after(30, self._tick)
        except ValueError as ve:
            messagebox.showwarning("Simulación", str(ve))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _tick(self):
        if not self.anim_running:
            return
        if self.anim_paused:
            self.after(60, self._tick)
            return

        i = self.anim_idx

        # Cortar al impacto
        ia = min(i, self.impact_idx_att)
        idf = min(i, self.impact_idx_def)

        # Actualizar trayectorias hasta los índices actuales
        self.line_att.set_data(self.A.x[:ia+1], self.A.y[:ia+1])
        self.line_def.set_data(self.D.x[:idf+1], self.D.y[:idf+1])

        # Actualizar flechas (dirección "instantánea")
        if ia >= 1:
            x_prev, y_prev = self.A.x[ia-1], self.A.y[ia-1]
            x_curr, y_curr = self.A.x[ia], self.A.y[ia]
            self.quiver_att.set_positions((x_prev, y_prev), (x_curr, y_curr))
        if idf >= 1:
            x_prev, y_prev = self.D.x[idf-1], self.D.y[idf-1]
            x_curr, y_curr = self.D.x[idf], self.D.y[idf]
            self.quiver_def.set_positions((x_prev, y_prev), (x_curr, y_curr))

        # Pintar impacto al final
        if ia == self.impact_idx_att and idf == self.impact_idx_def:
            self.pt_impact.set_data([self.impact[0]], [self.impact[1]])
            self.anim_running = False  # ← detener exactamente en la intercepción

        self.canvas.draw_idle()
        self.anim_idx += 1

        if self.anim_running:
            self.after(30, self._tick)

    def on_pause(self):
        if not self.anim_running:
            return
        self.anim_paused = not self.anim_paused
        self.btn_pause.config(text="Reanudar" if self.anim_paused else "Pausar")

    def on_reset(self):
        self.anim_running = False
        self.anim_paused = False
        self.anim_idx = 0
        self.ax.clear()
        self.ax.set_xlabel("x [m]")
        self.ax.set_ylabel("y [m]")
        self.ax.set_title("Listo para simular")
        self.canvas.draw()
        self.lbl_suggestion.config(text="", foreground="")

if __name__ == "__main__":
    App().mainloop()


