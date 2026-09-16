# Approximations: Pure Newtonian gravity (no GR correction), classical Hookean cohesion model, rigid host planet.

"""
Phaethon: Roche Limit & Tidal Disruption Engine (NASA Edition)
=============================================================
Main Application Entry Point.

Usage:
  python main.py             Launch NASA-Grade 3D Shader Engine with DearPyGui Control Panel
  python main.py --web       Launch WebGL 3D Interactive Browser Visualizer
  python main.py --test      Run pytest physics verification test suite
  python main.py --headless  Run headless 2,000-step energy drift benchmark
"""

import sys
import os
import argparse
import webbrowser
import http.server
import socketserver
import numpy as np
import pygame
from pygame.locals import *

import dearpygui.dearpygui as dpg

from phaethon.simulation import SimulationApp
from phaethon.pbr_renderer import PBRShaderRenderer
from phaethon.gui import SciFiGuiDashboard

def start_web_server(port: int = 8000):
    web_dir = os.path.join(os.path.dirname(__file__), "web")
    os.chdir(web_dir)
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    print(f"\n[PHAETHON WEBGL SERVER] Serving at http://localhost:{port}")
    webbrowser.open(f"http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping WebGL server.")
        httpd.server_close()


def run_headless_benchmark(steps: int = 2000):
    print("=" * 70)
    print("PHAETHON: HEADLESS BENCHMARK & HAMILTONIAN ENERGY CONSERVATION TEST")
    print("Approximations: Pure Newtonian gravity (no GR correction), classical Hookean cohesion model, rigid host planet.")
    print("=" * 70)

    app = SimulationApp(num_particles=150, initial_radius=12.0)
    app.decay_on = False
    app.integrator.set_decay_rate(0.0)
    E0 = app.integrator.initial_energy
    roche = app.integrator.compute_roche_limit()

    print(f"Initial Total Energy: {E0:.6f}")
    print(f"Theoretical Roche Limit: {roche:.3f} AU")
    print(f"Running {steps} Symplectic Velocity Verlet integration steps (dt=0.001)...")

    for s in range(steps):
        app.integrator.step(0.0008)

    telem = app.integrator.get_telemetry()
    print("-" * 70)
    print(f"Final Step {steps}:")
    print(f"  Orbital Radius:    {telem['orbital_radius']:.4f} AU")
    print(f"  Final Energy:      {telem['total_energy']:.6f}")
    print(f"  Total Energy Drift: {telem['energy_drift']:.6e}")
    print(f"  Active Spring Bonds: {telem['active_bonds']} / {telem['total_bonds']}")
    print("-" * 70)
    if telem['energy_drift'] < 1e-4:
        print("SUCCESS: Hamiltonian energy conservation requirement satisfied (|dE|/|E0| < 1e-4).")
    else:
        print("WARNING: Energy drift exceeded threshold.")
    print("=" * 70)


def run_interactive_simulation(args):
    pygame.init()
    width, height = args.width, args.height

    pygame.display.set_caption("Phaethon: Roche Limit & Tidal Disruption Engine (NASA Edition)")
    flags = DOUBLEBUF | OPENGL | RESIZABLE
    screen = pygame.display.set_mode((width, height), flags)

    app = SimulationApp(
        num_particles=args.particles,
        initial_radius=12.0,
        decay_rate=0.006,
        dt=0.002
    )
    renderer = PBRShaderRenderer(width=width, height=height)
    gui = SciFiGuiDashboard(app, renderer)

    clock = pygame.time.Clock()
    running = True

    print("\n" + "=" * 70)
    print("PHAETHON: ROCHE LIMIT & TIDAL DISRUPTION ENGINE (NASA EDITION)")
    print("Approximations: Pure Newtonian gravity (no GR correction), classical Hookean cohesion model, rigid host planet.")
    print("=" * 70)
    print("CONTROLS:")
    print("  [DearPyGui Window] : Adjust Cohesion k, Decay Rate, Time Speed, Viewport Selector, Live Energy Chart")
    print("  [V]                : Toggle Live Tidal Stress Differential Vector Field (3D Force Arrows)")
    print("  [Space]            : Toggle Pause / Resume")
    print("  [D]                : Toggle Orbital Decay Spiral ON / OFF")
    print("  [C]                : Toggle Color Mode (GRAVITATIONAL STRESS vs VELOCITY)")
    print("  [R]                : Reset Simulation State")
    print("  [1 - 4]            : Select NASA Viewports (Planet, Cinematic, Moon Lock, Debris Stream)")
    print("  Mouse Drag / Scroll: Arcball Camera Orbit, Pan, and Zoom with Momentum")
    print("=" * 70 + "\n")

    while running and dpg.is_dearpygui_running():
        dt_frame = clock.tick(args.fps) / 1000.0
        fps = clock.get_fps()

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == VIDEORESIZE:
                renderer.resize(event.w, event.h)
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_SPACE:
                    app.toggle_pause()
                elif event.key == K_d:
                    app.toggle_decay()
                elif event.key == K_v:
                    renderer.show_vectors = not renderer.show_vectors
                elif event.key == K_c:
                    renderer.color_mode = 1 if renderer.color_mode == 0 else 0
                elif event.key == K_r:
                    app.reset()
                elif event.key == K_1:
                    renderer.camera.track_mode = "PLANET"
                    renderer.camera.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
                elif event.key == K_2:
                    renderer.camera.track_mode = "PLANET"
                    renderer.camera.yaw, renderer.camera.pitch, renderer.camera.distance = 35.0, 15.0, 28.0
                elif event.key == K_3:
                    renderer.camera.track_mode = "MOON"
                elif event.key == K_4:
                    renderer.camera.track_mode = "DEBRIS"

            renderer.camera.handle_event(event)

        app.update(sub_steps=4)
        telem = app.integrator.get_telemetry()

        renderer.camera.update(dt_frame, telem)
        renderer.time_val += dt_frame

        gui.update_telemetry(telem, app.simulation_time)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        renderer.camera.apply_transform()
        renderer.render_skybox()
        renderer.render_pbr_planet(radius=2.0)
        renderer.render_roche_equipotential_shell(roche_radius=app.integrator.compute_roche_limit())
        renderer.render_tidal_vector_field(app.integrator)
        renderer.render_thermal_particles_and_asteroids(app.integrator)
        renderer.render_disruption_screen_flash()

        pygame.display.flip()
        dpg.render_dearpygui_frame()

    dpg.destroy_context()
    pygame.quit()


def main():
    parser = argparse.ArgumentParser(description="Phaethon: Roche Limit & Tidal Disruption Engine (NASA Edition)")
    parser.add_argument("--web", action="store_true", help="Launch WebGL 3D Interactive Browser Visualizer")
    parser.add_argument("--test", action="store_true", help="Run pytest verification test suite")
    parser.add_argument("--headless", action="store_true", help="Run non-GUI benchmark test")
    parser.add_argument("--particles", type=int, default=200, help="Number of moon sub-particles (100 to 300)")
    parser.add_argument("--fps", type=int, default=60, help="Target frame rate")
    parser.add_argument("--width", type=int, default=1280, help="Window width")
    parser.add_argument("--height", type=int, default=720, help="Window height")

    args = parser.parse_args()

    if args.web:
        start_web_server()
    elif args.test:
        import pytest
        sys.exit(pytest.main(["-v", "tests/test_simulation.py"]))
    elif args.headless:
        run_headless_benchmark()
    else:
        run_interactive_simulation(args)


if __name__ == "__main__":
    main()
