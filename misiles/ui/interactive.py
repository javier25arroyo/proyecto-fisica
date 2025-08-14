from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import math
from typing import Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button, TextBox

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


class DefenderInfoPanel:
    def __init__(self, fig, initial_values):
        self.fig = fig
        
        # Crear panel de información del defensor
        self.panel_ax = fig.add_axes([0.02, 0.02, 0.22, 0.56])
        self.panel_ax.set_xlim(0, 1)
        self.panel_ax.set_ylim(0, 1)
        self.panel_ax.axis('off')
        
        # Título del panel
        self.panel_ax.text(0.5, 0.95, '🛡️ SISTEMA DEFENSOR', 
                          fontsize=11, weight='bold', ha='center', transform=self.panel_ax.transAxes,
                          bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))
        
        # Información actual del defensor
        self.info_texts = {}
        
        # Posición
        self.info_texts['pos'] = self.panel_ax.text(0.05, 0.85, '', fontsize=9, 
                                                   transform=self.panel_ax.transAxes)
        
        # Velocidad máxima
        self.info_texts['vel'] = self.panel_ax.text(0.05, 0.78, '', fontsize=9, 
                                                   transform=self.panel_ax.transAxes)
        
        # Alcance estimado
        self.info_texts['range'] = self.panel_ax.text(0.05, 0.71, '', fontsize=9, 
                                                     transform=self.panel_ax.transAxes)
        
        # Tiempo de reacción
        self.info_texts['reaction'] = self.panel_ax.text(0.05, 0.64, '', fontsize=9, 
                                                        transform=self.panel_ax.transAxes)
        
        # Precisión
        self.info_texts['precision'] = self.panel_ax.text(0.05, 0.57, '', fontsize=9, 
                                                          transform=self.panel_ax.transAxes)
        
        # Estado del sistema
        self.status_box = self.panel_ax.text(0.5, 0.45, 'Sistema Listo', fontsize=10, 
                                           ha='center', transform=self.panel_ax.transAxes,
                                           bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen"))
        
        # Ventajas del defensor
        advantages_text = ("🎯 VENTAJAS DEFENSORAS:\n"
                          "• Detección temprana\n"
                          "• Velocidad superior\n"
                          "• Posición estratégica\n"
                          "• Tiempo de reacción optimizado")
        self.panel_ax.text(0.05, 0.35, advantages_text, fontsize=8, 
                          transform=self.panel_ax.transAxes, verticalalignment='top',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))
        
        # Instrucciones de uso
        instructions_text = ("📋 INSTRUCCIONES:\n"
                           "1. Configure el atacante ➡️\n"
                           "2. Ajuste defensor con sliders ⬇️\n"
                           "3. Presione DISPARAR 🚀\n"
                           "4. Observe interceptación 💥")
        self.panel_ax.text(0.05, 0.15, instructions_text, fontsize=8, 
                          transform=self.panel_ax.transAxes, verticalalignment='top',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcyan", alpha=0.8))
    
    def update_info(self, def_x0, def_spring_x, def_mass, v0_max, max_range, reaction_time, precision):
        # Actualizar información del defensor
        self.info_texts['pos'].set_text(f"📍 Posición: ({def_x0:.1f}, 0.0) m")
        self.info_texts['vel'].set_text(f"🚀 Vel. Máxima: {v0_max:.1f} m/s")
        self.info_texts['range'].set_text(f"🎯 Alcance: ~{max_range:.0f} m")
        self.info_texts['reaction'].set_text(f"⏱️ Reacción: {reaction_time:.1f} s")
        self.info_texts['precision'].set_text(f"🎪 Precisión: ±{precision:.1f} m")
        
        # Actualizar color del estado según capacidades
        if v0_max > 50 and reaction_time < 5:
            self.status_box.set_text("🛡️ Sistema Óptimo")
            self.status_box.set_bbox(dict(boxstyle="round,pad=0.3", facecolor="lightgreen"))
        elif v0_max > 30:
            self.status_box.set_text("⚡ Sistema Activo")
            self.status_box.set_bbox(dict(boxstyle="round,pad=0.3", facecolor="yellow"))
        else:
            self.status_box.set_text("⚠️ Capacidad Limitada")
            self.status_box.set_bbox(dict(boxstyle="round,pad=0.3", facecolor="orange"))


class AttackerInputPanel:
    def __init__(self, fig, initial_values, on_update_callback, on_fire_callback):
        self.fig = fig
        self.on_update = on_update_callback
        self.on_fire = on_fire_callback
        
        # Crear panel de entrada de datos del atacante
        self.panel_ax = fig.add_axes([0.02, 0.60, 0.22, 0.38])
        self.panel_ax.set_xlim(0, 1)
        self.panel_ax.set_ylim(0, 1)
        self.panel_ax.axis('off')
        
        # Título del panel
        self.panel_ax.text(0.5, 0.95, '🚀 MISIL ATACANTE', 
                          fontsize=11, weight='bold', ha='center', transform=self.panel_ax.transAxes,
                          bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral"))
        
        # Campos de entrada de texto con descripciones amigables
        y_positions = [0.85, 0.75, 0.65, 0.55, 0.45]
        labels = ['📍 Posición X (m):', '📐 Altura Y (m):', '🎯 Ángulo disparo (°):', '🔧 Potencia resorte (m):', '⚖️ Masa proyectil (kg):']
        
        self.textboxes = {}
        self.labels = {}
        
        for i, (label, y_pos) in enumerate(zip(labels, y_positions)):
            # Etiqueta
            self.panel_ax.text(0.05, y_pos + 0.03, label, fontsize=9, transform=self.panel_ax.transAxes)
            
            # Caja de texto
            textbox_ax = fig.add_axes([0.04, 0.60 + (y_pos - 0.02) * 0.38, 0.18, 0.025])
            
            if i == 0:  # x0
                initial_val = str(initial_values.get('x0', 0.0))
                textbox = TextBox(textbox_ax, '', initial=initial_val)
                textbox.on_submit(self._on_x0_submit)
                self.textboxes['x0'] = textbox
            elif i == 1:  # y0
                initial_val = str(initial_values.get('y0', 0.0))
                textbox = TextBox(textbox_ax, '', initial=initial_val)
                textbox.on_submit(self._on_y0_submit)
                self.textboxes['y0'] = textbox
            elif i == 2:  # theta
                initial_val = str(initial_values.get('theta_deg', 45.0))
                textbox = TextBox(textbox_ax, '', initial=initial_val)
                textbox.on_submit(self._on_theta_submit)
                self.textboxes['theta'] = textbox
            elif i == 3:  # spring x
                initial_val = str(initial_values.get('spring_x', 0.5))
                textbox = TextBox(textbox_ax, '', initial=initial_val)
                textbox.on_submit(self._on_spring_x_submit)
                self.textboxes['spring_x'] = textbox
            elif i == 4:  # mass
                initial_val = str(initial_values.get('mass', 10.0))
                textbox = TextBox(textbox_ax, '', initial=initial_val)
                textbox.on_submit(self._on_mass_submit)
                self.textboxes['mass'] = textbox
        
        # Botón de disparo grande y prominente
        fire_btn_ax = fig.add_axes([0.04, 0.62, 0.18, 0.06])
        self.fire_btn = Button(fire_btn_ax, '🚀 DISPARAR', color='red', hovercolor='darkred')
        self.fire_btn.label.set_fontsize(12)
        self.fire_btn.label.set_weight('bold')
        self.fire_btn.label.set_color('white')
        self.fire_btn.on_clicked(self._on_fire_clicked)
        
        # Información de estado
        self.status_text = self.panel_ax.text(0.5, 0.30, '✅ Listo para disparar', 
                                            fontsize=9, ha='center', transform=self.panel_ax.transAxes,
                                            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen"))
        
        # Información del misil actual
        self.missile_info = self.panel_ax.text(0.5, 0.20, '', fontsize=8, ha='center', 
                                             transform=self.panel_ax.transAxes,
                                             bbox=dict(boxstyle="round,pad=0.2", facecolor="lightyellow", alpha=0.8))
        
        # Instrucciones mejoradas
        instructions = ("💡 OPCIONES DE DISPARO:\n"
                       "🔸 Configure valores y presione DISPARAR\n"
                       "🔸 Haga clic directamente en el mapa\n"
                       "🔸 Interceptación automática garantizada")
        self.panel_ax.text(0.05, 0.12, instructions, fontsize=7, 
                          transform=self.panel_ax.transAxes, verticalalignment='top',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcyan", alpha=0.9))
    
    def _on_x0_submit(self, val):
        try:
            x0 = float(val)
            self.on_update('x0', x0)
        except ValueError:
            pass
    
    def _on_y0_submit(self, val):
        try:
            y0 = max(0.0, float(val))
            self.on_update('y0', y0)
        except ValueError:
            pass
    
    def _on_theta_submit(self, val):
        try:
            theta = max(5.0, min(85.0, float(val)))
            self.on_update('theta', theta)
        except ValueError:
            pass
    
    def _on_spring_x_submit(self, val):
        try:
            spring_x = max(0.05, min(1.0, float(val)))
            self.on_update('spring_x', spring_x)
        except ValueError:
            pass
    
    def _on_mass_submit(self, val):
        try:
            mass = max(1.0, float(val))
            self.on_update('mass', mass)
        except ValueError:
            pass
    
    def _on_fire_clicked(self, event):
        # Actualizar todos los valores antes de disparar
        self._update_all_values()
        self.update_status("🚀 Disparando...", "orange")
        self.on_fire()
    
    def _update_all_values(self):
        # Actualizar todos los valores desde las cajas de texto
        try:
            self._on_x0_submit(self.textboxes['x0'].text)
            self._on_y0_submit(self.textboxes['y0'].text)
            self._on_theta_submit(self.textboxes['theta'].text)
            self._on_spring_x_submit(self.textboxes['spring_x'].text)
            self._on_mass_submit(self.textboxes['mass'].text)
        except:
            pass
    
    def update_status(self, message, color="lightblue"):
        self.status_text.set_text(message)
        self.status_text.set_bbox(dict(boxstyle="round,pad=0.3", facecolor=color))
        self.fig.canvas.draw_idle()
    
    def update_values(self, values):
        self.textboxes['x0'].set_val(str(values.get('x0', 0.0)))
        self.textboxes['y0'].set_val(str(values.get('y0', 0.0)))
        self.textboxes['theta'].set_val(str(values.get('theta_deg', 45.0)))
        self.textboxes['spring_x'].set_val(str(values.get('spring_x', 0.5)))
        self.textboxes['mass'].set_val(str(values.get('mass', 10.0)))
        
        # Actualizar información del misil
        self.update_missile_info(values)
    
    def update_missile_info(self, values):
        """Actualizar información calculada del misil atacante"""
        try:
            from ..core.springs import Spring
            
            # Calcular velocidad inicial estimada
            k = 20000.0  # Valor por defecto de baseline.json
            spring = Spring(k=k, x=values.get('spring_x', 0.5), m=values.get('mass', 10.0))
            v0 = spring.v0
            
            # Estimar alcance máximo (proyectil a 45°)
            g = 9.81
            max_range = (v0 * v0) / g
            
            info_text = f"🚀 Vel: {v0:.1f} m/s | 🎯 Alcance: ~{max_range:.0f} m"
            self.missile_info.set_text(info_text)
            
        except Exception:
            self.missile_info.set_text("🚀 Calculando parámetros...")


class InteractiveApp:
    def __init__(self):
        # cargar escenario por defecto
        scen_path = Path(__file__).resolve().parent.parent / 'scenarios' / 'baseline.json'
        with open(scen_path, 'r', encoding='utf-8') as f:
            self.scen = load_scenario(json.load(f))

        # figura y ejes
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.ax.set_xlabel('x [m]')
        self.ax.set_ylabel('y [m]')
        self.ax.grid(True)
        self.ax.set_aspect('equal', adjustable='box')
        plt.subplots_adjust(left=0.26, right=0.98, top=0.90, bottom=0.44)
        
        # valores actuales del atacante para el panel
        self.attacker_values = {
            'x0': self.scen.attacker.x0,
            'y0': self.scen.attacker.y0,
            'theta_deg': self.scen.attacker.theta_deg or 45.0,
            'spring_x': self.scen.attacker.spring.x,
            'mass': self.scen.attacker.spring.m
        }
        
        # crear panel de entrada del atacante
        self.attacker_panel = AttackerInputPanel(
            self.fig, 
            self.attacker_values, 
            self._on_attacker_param_change,
            self._on_fire_attack
        )
        
        # crear panel de información del defensor
        self.defender_panel = DefenderInfoPanel(self.fig, {})

        # líneas y marcadores
        (self.att_line,) = self.ax.plot([], [], '-', color='red', linewidth=2, label='🚀 Misil Atacante')
        (self.def_line,) = self.ax.plot([], [], '--', color='blue', linewidth=2, label='🛡️ Misil Defensor')
        (self.att_pt,) = self.ax.plot([], [], 'o', color='red', markersize=8)
        (self.def_pt,) = self.ax.plot([], [], 'o', color='blue', markersize=8)
        
        # Marcadores de posiciones de lanzamiento
        self.att_launch_marker = self.ax.scatter([], [], marker='^', s=150, color='darkred', 
                                               zorder=10, label='🎯 Lanzador Atacante', edgecolors='white', linewidth=2)
        self.def_launch_marker = self.ax.scatter([], [], marker='s', s=150, color='darkblue', 
                                               zorder=10, label='🏰 Base Defensora', edgecolors='white', linewidth=2)
        
        # Punto de impacto/interceptación
        self.impact_scatter = self.ax.scatter([], [], marker='*', s=200, color='gold', 
                                            zorder=15, label='💥 Interceptación', edgecolors='red', linewidth=2)
        
        # Zona de alcance del defensor (círculo)
        self.defense_range_circle = plt.Circle((0, 0), 0, fill=False, color='lightblue', 
                                             linestyle=':', alpha=0.7, linewidth=2)
        self.ax.add_patch(self.defense_range_circle)
        
        # Etiquetas de texto en el mapa
        self.att_label = self.ax.text(0, 0, '', fontsize=9, ha='center', va='bottom',
                                     bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral", alpha=0.8))
        self.def_label = self.ax.text(0, 0, '', fontsize=9, ha='center', va='bottom',
                                     bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8))
        
        # Leyenda mejorada
        self.ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)

        # sliders (solo para defensor y configuración global)
        ax_defx0 = self.fig.add_axes([0.28, 0.34, 0.66, 0.03])
        ax_eps = self.fig.add_axes([0.28, 0.29, 0.66, 0.03])
        ax_dly = self.fig.add_axes([0.28, 0.24, 0.66, 0.03])
        ax_defx = self.fig.add_axes([0.28, 0.19, 0.66, 0.03])
        
        # Sliders ocultos para atacante (controlados por el panel)
        ax_ax0 = self.fig.add_axes([0.28, 0.14, 0.32, 0.025])
        ax_ay0 = self.fig.add_axes([0.62, 0.14, 0.32, 0.025])
        ax_theta = self.fig.add_axes([0.28, 0.09, 0.66, 0.025])
        ax_attx = self.fig.add_axes([0.28, 0.04, 0.32, 0.025])

        # Sliders principales (visibles) con etiquetas mejoradas
        self.s_defx0 = Slider(ax_defx0, '🏰 Posición Base Defensora [m]', -200.0, 200.0, valinit=self.scen.defender.x0)
        self.s_eps = Slider(ax_eps, '🎯 Precisión del Sistema [m] (menor = más preciso)', 0.1, 5.0, valinit=self.scen.globals.eps)
        self.s_delay = Slider(ax_dly, '⏱️ Tiempo Máximo de Reacción [s]', 0.0, 10.0, valinit=self.scen.globals.delay_max)
        self.s_defx = Slider(ax_defx, '🔧 Potencia del Misil Defensor [m]', 0.05, 1.0, valinit=self.scen.defender.spring.x)
        
        # Sliders ocultos para atacante (solo sincronización)
        self.s_attx0 = Slider(ax_ax0, '', -500.0, 500.0, valinit=self.scen.attacker.x0)
        self.s_atty0 = Slider(ax_ay0, '', 0.0, 200.0, valinit=self.scen.attacker.y0)  
        self.s_theta = Slider(ax_theta, '', 5.0, 85.0, valinit=self.scen.attacker.theta_deg or 45.0)
        self.s_attx = Slider(ax_attx, '', 0.05, 1.0, valinit=self.scen.attacker.spring.x)
        
        # Ocultar sliders del atacante
        for slider in [self.s_attx0, self.s_atty0, self.s_theta, self.s_attx]:
            slider.ax.set_visible(False)

        # botones
        ax_btn = self.fig.add_axes([0.45, 0.915, 0.20, 0.05])
        self.btn = Button(ax_btn, '🛡️ Calcular Interceptación')
        self.btn.label.set_fontsize(9)
        
        # botón de ayuda
        ax_help_btn = self.fig.add_axes([0.67, 0.915, 0.10, 0.05])
        self.help_btn = Button(ax_help_btn, '❓ Ayuda')
        self.help_btn.label.set_fontsize(9)
        self.help_btn.on_clicked(self._show_help)
        
        # ventana de ayuda (inicialmente oculta)
        self.help_window = None

        # estado animación
        self.anim: Optional[FuncAnimation] = None
        self.state = UIState([], [], [], None, None, None, None, '')

        # eventos
        self.btn.on_clicked(self.on_resolve)
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.on_click)

        # primer render
        self.on_resolve(None)

    def _show_help(self, event):
        """Mostrar ventana de ayuda con instrucciones detalladas"""
        import tkinter as tk
        from tkinter import messagebox
        
        try:
            # Crear ventana de ayuda
            if self.help_window is None or not self.help_window.winfo_exists():
                self.help_window = tk.Toplevel()
                self.help_window.title("🚀 Ayuda - Simulador de Misiles")
                self.help_window.geometry("600x500")
                self.help_window.configure(bg='white')
                
                # Crear scroll
                canvas = tk.Canvas(self.help_window, bg='white')
                scrollbar = tk.Scrollbar(self.help_window, orient="vertical", command=canvas.yview)
                scrollable_frame = tk.Frame(canvas, bg='white')
                
                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )
                
                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)
                
                # Contenido de ayuda
                help_text = """
🚀 SIMULADOR INTERACTIVO DE MISILES - GUÍA DE USO

═══════════════════════════════════════════════════════════

📋 DESCRIPCIÓN GENERAL
Este simulador permite configurar un misil atacante y observar cómo
un sistema defensor lo intercepta automáticamente.

═══════════════════════════════════════════════════════════

🎯 PANEL DEL ATACANTE (Lateral Derecho)

📍 Posición X/Y: Coordenadas de lanzamiento del misil atacante
   • X: Posición horizontal (-500 a 500 metros)
   • Y: Altura inicial (0 a 200 metros, 0 = suelo)

🎯 Ángulo de Disparo: Ángulo de lanzamiento (5° a 85°)
   • 45° = máximo alcance
   • Menor ángulo = trayectoria más plana
   • Mayor ángulo = trayectoria más alta

🔧 Potencia del Resorte: Compresión inicial (0.05 a 1.0 m)
   • Mayor compresión = mayor velocidad inicial
   • Afecta directamente el alcance del misil

⚖️ Masa del Proyectil: Peso del misil (mínimo 1 kg)
   • Mayor masa = menor velocidad (misma potencia)
   • Afecta la física del lanzamiento

═══════════════════════════════════════════════════════════

🛡️ PANEL DEL DEFENSOR (Lateral Izquierdo)

📊 Información en Tiempo Real:
   • Posición actual de la base defensora
   • Velocidad máxima del misil defensor
   • Alcance estimado del sistema
   • Tiempo de reacción configurado
   • Precisión del sistema

🎯 Ventajas Defensoras:
   • Detección temprana del atacante
   • Velocidad superior (generalmente)
   • Posición estratégica optimizable
   • Tiempo de reacción ajustable

═══════════════════════════════════════════════════════════

⚙️ CONTROLES DEL DEFENSOR (Sliders Inferiores)

🏰 Posición Base Defensora: Ubicación horizontal del defensor
   • Posicione estratégicamente para máxima cobertura

🎯 Precisión del Sistema: Tolerancia de error (menor = mejor)
   • Valores menores = interceptación más precisa
   • Afecta la probabilidad de éxito

⏱️ Tiempo de Reacción: Demora máxima para responder
   • Tiempo desde detección hasta disparo
   • Menor tiempo = mejor capacidad defensiva

🔧 Potencia del Misil Defensor: Energía del sistema defensivo
   • Mayor potencia = mayor velocidad y alcance

═══════════════════════════════════════════════════════════

🚀 CÓMO DISPARAR

Método 1 - Botón DISPARAR:
   1. Configure todos los parámetros del atacante
   2. Presione el botón rojo "🚀 DISPARAR"
   3. El sistema optimizará automáticamente la defensa

Método 2 - Clic en el Mapa:
   1. Haga clic directamente en cualquier punto del gráfico
   2. El atacante se posicionará ahí automáticamente
   3. La interceptación se calculará al instante

Método 3 - Recálculo Manual:
   • Use "🛡️ Calcular Interceptación" para recalcular
   • Útil después de ajustar parámetros del defensor

═══════════════════════════════════════════════════════════

💥 INTERPRETACIÓN DE RESULTADOS

🎯 Marcadores en el Mapa:
   • 🔺 Rojo: Posición de lanzamiento del atacante
   • 🟦 Azul: Base defensora
   • ⭐ Dorado: Punto de interceptación
   • Círculo punteado: Alcance máximo del defensor

📊 Trayectorias:
   • Línea roja sólida: Trayectoria del atacante
   • Línea azul punteada: Trayectoria del defensor
   • Puntos móviles: Misiles en vuelo (animación)

✅ Estados del Sistema:
   • Verde: Sistema óptimo, interceptación garantizada
   • Amarillo: Sistema activo, buenas capacidades
   • Naranja: Capacidad limitada, ajuste recomendado

═══════════════════════════════════════════════════════════

💡 CONSEJOS Y TRUCOS

🎯 Para Máxima Efectividad:
   • Posicione el defensor entre el atacante y objetivos críticos
   • Use ángulos de 30-60° para balance alcance/altura
   • Menor tiempo de reacción = mejor intercepción
   • La precisión alta (valores bajos) es crucial

🚀 Experimentación:
   • Pruebe diferentes combinaciones de parámetros
   • Observe cómo cambia el círculo de alcance defensivo
   • Note la influencia de la masa en la velocidad
   • Compare trayectorias con diferentes ángulos

⚠️ Limitaciones del Sistema:
   • El defensor siempre busca la intercepción óptima
   • En casos imposibles, optimiza automáticamente
   • La física simulada incluye gravedad realista
   • Los cálculos asumen condiciones ideales (sin viento)

═══════════════════════════════════════════════════════════

❓ ¿NECESITA MÁS AYUDA?

Si tiene problemas o preguntas adicionales:
   • Pruebe los valores por defecto primero
   • Experimente con configuraciones simples
   • Observe los indicadores de estado en tiempo real
   • Use la interceptación automática para casos complejos

¡Disfrute explorando la física de los misiles! 🚀
                """
                
                # Crear etiqueta con el texto
                label = tk.Label(scrollable_frame, text=help_text, 
                               font=("Courier", 10), bg='white', 
                               justify='left', wraplength=580)
                label.pack(padx=10, pady=10)
                
                # Configurar scroll
                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")
                
            else:
                # Si ya existe, traerla al frente
                self.help_window.lift()
                self.help_window.focus_force()
                
        except ImportError:
            # Si tkinter no está disponible, usar messagebox simple
            print("\n🚀 AYUDA RÁPIDA - SIMULADOR DE MISILES")
            print("=" * 50)
            print("• Configure parámetros del atacante en el panel derecho")
            print("• Presione '🚀 DISPARAR' para lanzar con interceptación automática")
            print("• Haga clic en el mapa para posicionar el atacante")
            print("• Ajuste sliders del defensor para experimentar")
            print("• El sistema garantiza interceptación exitosa")
            print("• Observe marcadores: 🔺=Atacante, 🟦=Defensor, ⭐=Interceptación")
        except Exception as e:
            print(f"Error mostrando ayuda: {e}")

    def _on_attacker_param_change(self, param, value):
        self.attacker_values[param] = value
        
        # sincronizar con sliders si es necesario
        if param == 'x0':
            self.s_attx0.set_val(value)
        elif param == 'y0':
            self.s_atty0.set_val(value)
        elif param == 'theta':
            self.s_theta.set_val(value)
        elif param == 'spring_x':
            self.s_attx.set_val(value)
        
        # actualizar información del misil atacante
        self.attacker_panel.update_missile_info(self.attacker_values)
        
        self.on_resolve(None)

    def _on_fire_attack(self):
        """Disparar atacante y calcular interceptación automáticamente"""
        # Actualizar estado
        self.attacker_panel.update_status("🎯 Calculando interceptación...", "yellow")
        
        # Intentar múltiples configuraciones del defensor para garantizar interceptación
        original_defx0 = self.s_defx0.val
        original_eps = self.s_eps.val
        original_delay = self.s_delay.val
        original_defx = self.s_defx.val
        
        # Calcular con configuración actual
        st = self.compute()
        
        # Si no hay interceptación, ajustar automáticamente parámetros del defensor
        if st.def_x is None or st.impact is None:
            self.attacker_panel.update_status("⚙️ Optimizando defensor...", "orange")
            
            # Intentar diferentes configuraciones
            configurations = [
                {'eps': 2.0, 'delay': 5.0, 'defx': 0.8},
                {'eps': 3.0, 'delay': 8.0, 'defx': 0.9},
                {'eps': 1.5, 'delay': 3.0, 'defx': 0.7},
                {'eps': 4.0, 'delay': 10.0, 'defx': 1.0},
            ]
            
            for config in configurations:
                self.s_eps.set_val(config['eps'])
                self.s_delay.set_val(config['delay'])
                self.s_defx.set_val(config['defx'])
                
                st = self.compute()
                if st.def_x is not None and st.impact is not None:
                    break
            
            # Si aún no hay interceptación, ajustar posición del defensor
            if st.def_x is None or st.impact is None:
                # Colocar defensor en posición estratégica
                att_x0 = self.attacker_values['x0']
                optimal_def_x0 = att_x0 + 50  # 50m adelante del atacante
                self.s_defx0.set_val(optimal_def_x0)
                st = self.compute()
        
        # Actualizar visualización
        self._update_display(st)
        
        if st.def_x is not None and st.impact is not None:
            self.attacker_panel.update_status("✅ ¡Interceptación exitosa!", "lightgreen")
        else:
            self.attacker_panel.update_status("❌ No se pudo interceptar", "lightcoral")

    def compute(self) -> UIState:
        g = self.scen.globals.g
        dt_sim = self.scen.globals.dt_sim
        dtheta = deg2rad(self.scen.globals.dtheta_deg)
        theta_min = deg2rad(5.0)
        theta_max = deg2rad(85.0)
        delay_min = 0.0
        delay_max = float(self.s_delay.val)

        # Actualizar springs con valores del panel del atacante
        att_sp = self.scen.attacker.spring
        def_sp = self.scen.defender.spring
        att_sp = type(att_sp)(k=att_sp.k, x=self.attacker_values['spring_x'], m=self.attacker_values['mass'])
        def_sp = type(def_sp)(k=def_sp.k, x=float(self.s_defx.val), m=def_sp.m)
        theta_a = deg2rad(self.attacker_values['theta_deg'])

        # v0 atacante y trayectoria
        v0_a = Spring(k=att_sp.k, x=att_sp.x, m=att_sp.m).v0
        x0_att = self.attacker_values['x0']
        y0_att = self.attacker_values['y0']
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
        x_val = float(event.xdata)
        y_val = max(0.0, float(event.ydata))
        
        # actualizar valores en el panel y sliders
        self.attacker_values['x0'] = x_val
        self.attacker_values['y0'] = y_val
        self.s_attx0.set_val(x_val)
        self.s_atty0.set_val(y_val)
        self.attacker_panel.update_values(self.attacker_values)
        self.on_resolve(None)

    def _update_display(self, st):
        """Actualizar la visualización con el estado calculado"""
        # actualizar líneas de trayectoria
        self.att_line.set_data(st.att_x, st.att_y)
        if st.def_x is not None:
            self.def_line.set_data(st.def_x, st.def_y)
        else:
            self.def_line.set_data([], [])
        
        # actualizar punto de impacto
        if st.impact is not None:
            self.impact_scatter.set_offsets([st.impact])
        else:
            self.impact_scatter.set_offsets([])
        
        # actualizar marcadores de lanzamiento
        att_x0 = self.attacker_values['x0']
        att_y0 = self.attacker_values['y0']
        def_x0 = float(self.s_defx0.val)
        def_y0 = 0.0
        
        self.att_launch_marker.set_offsets([[att_x0, att_y0]])
        self.def_launch_marker.set_offsets([[def_x0, def_y0]])
        
        # actualizar etiquetas en el mapa
        self.att_label.set_position((att_x0, att_y0 + 5))
        self.att_label.set_text(f"🚀 ATACANTE\n({att_x0:.0f}, {att_y0:.0f})")
        
        self.def_label.set_position((def_x0, def_y0 + 10))
        self.def_label.set_text(f"🛡️ DEFENSOR\n({def_x0:.0f}, {def_y0:.0f})")
        
        # actualizar círculo de alcance del defensor
        from ..core.springs import Spring
        def_sp = self.scen.defender.spring
        def_spring = Spring(k=def_sp.k, x=float(self.s_defx.val), m=def_sp.m)
        v0d_max = def_spring.v0_max
        max_range = (v0d_max * v0d_max) / (2 * 9.81)  # Alcance estimado
        
        self.defense_range_circle.center = (def_x0, def_y0)
        self.defense_range_circle.radius = max_range
        
        # actualizar panel del defensor
        self.defender_panel.update_info(
            def_x0=def_x0,
            def_spring_x=float(self.s_defx.val),
            def_mass=def_sp.m,
            v0_max=v0d_max,
            max_range=max_range,
            reaction_time=float(self.s_delay.val),
            precision=float(self.s_eps.val)
        )
        
        # título mejorado
        title_parts = [
            f"🚀 Atacante: ({att_x0:.0f}, {att_y0:.0f})m",
            f"🛡️ Defensor: ({def_x0:.0f}, 0)m",
        ]
        if st.impact:
            title_parts.append(f"💥 Interceptación: ({st.impact[0]:.0f}, {st.impact[1]:.0f})m")
        
        self.fig.suptitle(" | ".join(title_parts), fontsize=12)

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

    def on_resolve(self, _):
        st = self.compute()
        self._update_display(st)
        # Actualizar estado en el panel solo si no fue un disparo automático
        if hasattr(self, 'attacker_panel'):
            if st.def_x is not None and st.impact is not None:
                self.attacker_panel.update_status("✅ Listo para disparar", "lightblue")
            else:
                self.attacker_panel.update_status("⚠️ Sin interceptación", "lightyellow")

    def run(self):
        plt.show()


def run():
    """Ejecutar la aplicación interactiva con panel de entrada del atacante"""
    print("🚀 Iniciando simulador interactivo de misiles...")
    print("✨ Panel de configuración del atacante disponible en la ventana")
    print("🎯 Use el botón DISPARAR para lanzar automáticamente con interceptación")
    InteractiveApp().run()

def run_enhanced():
    """Alias para la función run() mejorada"""
    run()


def interactive_attacker_setup():
    """
    Función interactiva para configurar parámetros del atacante desde consola.
    Retorna un diccionario con los parámetros configurados.
    """
    print("\n=== CONFIGURACIÓN INTERACTIVA DEL ATACANTE ===")
    print("Ingrese los parámetros del atacante (presione Enter para usar valor por defecto)")
    
    params = {}
    
    # Posición inicial X
    while True:
        try:
            x_input = input("Posición X inicial [m] (defecto: 0.0): ").strip()
            params['x0'] = float(x_input) if x_input else 0.0
            break
        except ValueError:
            print("Error: Ingrese un número válido")
    
    # Posición inicial Y
    while True:
        try:
            y_input = input("Posición Y inicial [m] (defecto: 0.0): ").strip()
            y_val = float(y_input) if y_input else 0.0
            params['y0'] = max(0.0, y_val)
            break
        except ValueError:
            print("Error: Ingrese un número válido")
    
    # Ángulo de disparo
    while True:
        try:
            theta_input = input("Ángulo de disparo [grados] (defecto: 45.0): ").strip()
            theta_val = float(theta_input) if theta_input else 45.0
            params['theta_deg'] = max(5.0, min(85.0, theta_val))
            if theta_val != params['theta_deg']:
                print(f"Ángulo limitado a rango [5.0, 85.0]: {params['theta_deg']}")
            break
        except ValueError:
            print("Error: Ingrese un número válido")
    
    # Compresión del resorte
    while True:
        try:
            x_spring_input = input("Compresión del resorte [m] (defecto: 0.5): ").strip()
            x_spring_val = float(x_spring_input) if x_spring_input else 0.5
            params['spring_x'] = max(0.05, min(1.0, x_spring_val))
            if x_spring_val != params['spring_x']:
                print(f"Compresión limitada a rango [0.05, 1.0]: {params['spring_x']}")
            break
        except ValueError:
            print("Error: Ingrese un número válido")
    
    # Masa del proyectil
    while True:
        try:
            mass_input = input("Masa del proyectil [kg] (defecto: 10.0): ").strip()
            mass_val = float(mass_input) if mass_input else 10.0
            params['mass'] = max(1.0, mass_val)
            if mass_val != params['mass']:
                print(f"Masa limitada a mínimo 1.0 kg: {params['mass']}")
            break
        except ValueError:
            print("Error: Ingrese un número válido")
    
    print("\n=== PARÁMETROS CONFIGURADOS ===")
    print(f"Posición inicial: ({params['x0']:.2f}, {params['y0']:.2f}) m")
    print(f"Ángulo de disparo: {params['theta_deg']:.2f}°")
    print(f"Compresión del resorte: {params['spring_x']:.3f} m")
    print(f"Masa del proyectil: {params['mass']:.2f} kg")
    
    return params


if __name__ == '__main__':
    run()
