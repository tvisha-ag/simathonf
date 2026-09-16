# Approximations: Pure Newtonian gravity (no GR correction), classical Hookean cohesion model, rigid host planet.

"""
Phaethon NASA-Grade DearPyGui Glassmorphic Telemetry Dashboard
--------------------------------------------------------------
Interactive Sci-Fi Control Panel providing parameter controls (Cohesion Strength,
Orbital Decay, Mass Ratio, Time Speed), Tidal Vector Field Toggle,
Roche Radius vs Distance Bar, Viewport Selector ("Cinematic Orbit", "Moon Lock",
"Debris Stream Focus", "Planet Origin"), and Real-Time Mechanical Energy Drift Chart.
"""

import numpy as np
import dearpygui.dearpygui as dpg

class SciFiGuiDashboard:
    """
    Manages NASA-grade DearPyGui glassmorphic control dashboard, real-time energy chart,
    tensional stress gauge, and camera viewport selectors.
    """
    def __init__(self, sim_app, renderer):
        self.sim = sim_app
        self.renderer = renderer

        self.max_plot_pts = 300
        self.time_history = list(np.zeros(self.max_plot_pts))
        self.energy_drift_history = list(np.zeros(self.max_plot_pts))

        self._build_gui()

    def _build_gui(self):
        dpg.create_context()

        # NASA Glassmorphism Dark Mode Theme
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (10, 14, 22, 220))
                dpg.add_theme_color(dpg.mvThemeCol_Header, (25, 40, 65, 240))
                dpg.add_theme_color(dpg.mvThemeCol_Button, (30, 60, 100, 220))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (50, 100, 160, 250))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (70, 130, 200, 255))
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (16, 24, 38, 220))
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (0, 180, 240, 255))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (230, 240, 255, 255))
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)

        dpg.bind_theme(global_theme)

        # 1. Main Telemetry & Control Panel Window
        with dpg.window(label="NASA EYES :: PHAETHON TELEMETRY DASHBOARD", pos=(15, 15), width=430, height=690, no_close=True):
            dpg.add_text("PHYSICS & ORBITAL PARAMETERS", color=(255, 215, 0))
            dpg.add_separator()

            # Moon Cohesion Strength Slider
            dpg.add_slider_float(
                label="Moon Cohesion (k_cohesion)",
                default_value=self.sim.moon.k_spring,
                min_value=0.0,
                max_value=300.0,
                callback=self._cb_cohesion
            )

            # Orbital Decay Rate Slider
            dpg.add_slider_float(
                label="Orbital Decay Rate",
                default_value=self.sim.default_decay_rate,
                min_value=0.0,
                max_value=0.03,
                format="%.4f",
                callback=self._cb_decay_rate
            )

            # Mass Ratio (M_planet / m_moon)
            dpg.add_slider_float(
                label="Mass Ratio (M_p / m_m)",
                default_value=1000.0,
                min_value=200.0,
                max_value=5000.0,
                callback=self._cb_mass_ratio
            )

            # Timestep Speed Multiplier
            dpg.add_combo(
                items=["0.0x (Pause)", "0.5x Real-Time", "1.0x Real-Time", "2.0x Fast", "5.0x Hyper"],
                default_value="1.0x Real-Time",
                label="Time Speed",
                callback=self._cb_time_speed
            )

            # Camera Viewport Selector (NASA Presets)
            dpg.add_combo(
                items=["Planet Origin", "Cinematic Orbit", "Moon Lock", "Debris Stream Focus"],
                default_value="Planet Origin",
                label="Camera Viewport",
                callback=self._cb_camera_viewport
            )

            # Toggles
            dpg.add_checkbox(label="Live Tidal Differential Vector Field (3D Force Arrows)", default_value=self.renderer.show_vectors, callback=self._cb_toggle_vectors)
            dpg.add_checkbox(label="Enable Orbital Decay Spiral", default_value=self.sim.decay_on, callback=self._cb_toggle_decay)
            dpg.add_checkbox(label="Volumetric Roche Equipotential Shell", default_value=self.renderer.show_roche, callback=self._cb_toggle_roche)
            dpg.add_checkbox(label="Celestial Star Grid & Skybox", default_value=self.renderer.show_grid, callback=self._cb_toggle_grid)
            dpg.add_checkbox(label="Cohesive Spring Bonds", default_value=self.renderer.show_bonds, callback=self._cb_toggle_bonds)

            dpg.add_spacer(height=8)
            dpg.add_text("TELEMETRY GAUGES & ROCHE BOUNDARY", color=(255, 215, 0))
            dpg.add_separator()

            # Active Roche Radius vs Distance Bar
            self.dist_bar = dpg.add_progress_bar(label="Orbital Distance vs Roche Radius", default_value=0.2, width=390)
            self.status_text = dpg.add_text("Status: STABLE ORBITAL HYDROSTATIC BALANCE", color=(60, 240, 150))
            self.diff_text = dpg.add_text("Tidal Differential (Δa): 0.3842 AU/s²", color=(200, 220, 255))

            dpg.add_spacer(height=8)
            dpg.add_text("REAL-TIME MECHANICAL ENERGY DRIFT CHART", color=(255, 215, 0))
            dpg.add_separator()

            # Real-Time Mechanical Energy Drift Chart Plot
            with dpg.plot(label="Total Energy Drift (|dE|/|E0|)", height=150, width=390):
                dpg.add_plot_legend()
                self.x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Sim Time (s)")
                self.y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Relative Drift")
                self.drift_line = dpg.add_line_series(self.time_history, self.energy_drift_history, parent=self.y_axis, label="Energy Drift")

            # Reset Button
            dpg.add_spacer(height=8)
            dpg.add_button(label="RESET SIMULATION STATE", width=390, height=35, callback=self._cb_reset)

        dpg.create_viewport(title="Phaethon: Roche Limit & Tidal Disruption Engine (NASA Edition)", width=1280, height=720)
        dpg.setup_dearpygui()

    def _cb_cohesion(self, sender, app_data):
        self.sim.integrator.set_cohesion_k(app_data)

    def _cb_decay_rate(self, sender, app_data):
        self.sim.default_decay_rate = app_data
        if self.sim.decay_on:
            self.sim.integrator.set_decay_rate(app_data)

    def _cb_mass_ratio(self, sender, app_data):
        self.sim.integrator.M_host = float(app_data)

    def _cb_time_speed(self, sender, app_data):
        if "0.0x" in app_data:
            self.sim.paused = True
        else:
            self.sim.paused = False

    def _cb_camera_viewport(self, sender, app_data):
        if "Planet" in app_data:
            self.renderer.camera.track_mode = "PLANET"
        elif "Cinematic" in app_data:
            self.renderer.camera.track_mode = "PLANET"
            self.renderer.camera.yaw, self.renderer.camera.pitch, self.renderer.camera.distance = 35.0, 15.0, 28.0
        elif "Moon" in app_data:
            self.renderer.camera.track_mode = "MOON"
        elif "Debris" in app_data:
            self.renderer.camera.track_mode = "DEBRIS"

    def _cb_toggle_vectors(self, sender, app_data):
        self.renderer.show_vectors = bool(app_data)

    def _cb_toggle_decay(self, sender, app_data):
        self.sim.decay_on = bool(app_data)
        if self.sim.decay_on:
            self.sim.integrator.set_decay_rate(self.sim.default_decay_rate)
        else:
            self.sim.integrator.set_decay_rate(0.0)

    def _cb_toggle_grid(self, sender, app_data):
        self.renderer.show_grid = bool(app_data)

    def _cb_toggle_roche(self, sender, app_data):
        self.renderer.show_roche = bool(app_data)

    def _cb_toggle_bonds(self, sender, app_data):
        self.renderer.show_bonds = bool(app_data)

    def _cb_reset(self, sender, app_data):
        self.sim.reset()
        self.time_history = list(np.zeros(self.max_plot_pts))
        self.energy_drift_history = list(np.zeros(self.max_plot_pts))

    def update_telemetry(self, telem: dict, sim_time: float):
        r_com = telem["orbital_radius"]
        r_roche = telem["roche_limit"]

        # Trigger screen flash on Roche disruption crossing
        if telem.get("flash_trigger", False):
            self.renderer.trigger_disruption_flash()

        # Distance vs Roche Radius Bar
        dist_ratio = min(1.0, max(0.05, (r_roche * 1.3) / max(0.1, r_com)))
        dpg.set_value(self.dist_bar, dist_ratio)

        dpg.set_value(self.diff_text, f"Tidal Differential (Δa): {telem['tidal_differential']:.4f} AU/s²")

        if telem["is_disrupted"]:
            dpg.set_value(self.status_text, "Status: CRITICAL TIDAL DISRUPTION & SHEAR RING")
            dpg.configure_item(self.status_text, color=(255, 60, 90))
        elif r_com < r_roche * 1.15:
            dpg.set_value(self.status_text, "Status: WARNING :: APPROACHING ROCHE LIMIT")
            dpg.configure_item(self.status_text, color=(255, 200, 50))
        else:
            dpg.set_value(self.status_text, "Status: STABLE ORBITAL HYDROSTATIC BALANCE")
            dpg.configure_item(self.status_text, color=(60, 240, 150))

        # Real-time Energy Drift Plot Update
        self.time_history.append(sim_time)
        self.energy_drift_history.append(telem["energy_drift"])
        if len(self.time_history) > self.max_plot_pts:
            self.time_history.pop(0)
            self.energy_drift_history.pop(0)

        dpg.set_value(self.drift_line, [self.time_history, self.energy_drift_history])
