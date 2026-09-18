# Approximations: Central Newtonian gravity with weak-field 1PN Schwarzschild perihelion precession correction term and N-body gravitational perturbation from a massive stellar intruder. Collisionless test-particle ring model.

"""
Phaethon: Relativistic Tidal Ring Disruption Engine
===================================================
Main Application Entry Point.

Usage:
  python main.py             Launch WebGL 3D Interactive Browser Visualizer
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

from phaethon.physics import G_CONST
from phaethon.simulation import SimulationApp

class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP Request Handler adding strict no-cache headers to prevent browser asset caching."""
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def start_web_server(port: int = 8000):
    web_dir = os.path.join(os.path.dirname(__file__), "web")
    os.chdir(web_dir)
    handler = NoCacheHTTPRequestHandler
    
    # Allow port reuse to prevent WinError 10048 when restarting quickly
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("", port), handler)
    print("=" * 70)
    print(f"PHAETHON WEBGL SERVER: http://localhost:{port}")
    print("Serving Relativistic Tidal Ring Disruption & Spacetime Engine...")
    print("=" * 70)
    webbrowser.open(f"http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping WebGL server.")
        httpd.server_close()


def run_headless_benchmark(steps: int = 2000):
    print("=" * 70)
    print("PHAETHON: HEADLESS BENCHMARK & HAMILTONIAN ENERGY CONSERVATION TEST")
    print("Model: Collisionless Test-Particle Tidal Ring under Central Black Hole Gravity (Isolated 1-Body Scenario)")
    print("=" * 70)

    app = SimulationApp(num_particles=1000, dt=0.0005, enable_gr=False)
    app.intruder.mass = 0.0  # Isolated 1-body orbit test for exact Hamiltonian energy conservation
    
    # Compute initial energy of particle 0
    pos = app.ring.positions[0]
    vel = app.ring.velocities[0]
    r0 = np.linalg.norm(pos)
    v0 = np.linalg.norm(vel)
    E0 = 0.5 * (v0 ** 2) - G_CONST * app.bh.mass / r0

    print(f"Initial Specific Orbital Energy: {E0:.6f} AU^2 / yr^2")
    print(f"Running {steps} Symplectic Velocity Verlet integration steps (dt=0.0005 yr)...")

    for _ in range(steps):
        app.integrator.step(0.0005)

    pos_f = app.ring.positions[0]
    vel_f = app.ring.velocities[0]
    rf = np.linalg.norm(pos_f)
    vf = np.linalg.norm(vel_f)
    Ef = 0.5 * (vf ** 2) - G_CONST * app.bh.mass / rf

    energy_drift = abs(Ef - E0) / abs(E0)

    print("-" * 70)
    print(f"Final Step {steps}:")
    print(f"  Final Energy:      {Ef:.6f}")
    print(f"  Energy Drift |dE/E0|: {energy_drift:.6e}")
    print("-" * 70)
    if energy_drift < 1e-4:
        print("SUCCESS: Symplectic Verlet Hamiltonian energy conservation satisfied (|dE/E0| < 1e-4).")
    else:
        print("WARNING: Energy drift exceeded threshold.")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Phaethon: Relativistic Tidal Ring Disruption Engine")
    parser.add_argument("--web", action="store_true", help="Launch WebGL 3D Interactive Browser Visualizer")
    parser.add_argument("--test", action="store_true", help="Run pytest verification test suite")
    parser.add_argument("--headless", action="store_true", help="Run non-GUI benchmark test")
    parser.add_argument("--port", type=int, default=8000, help="Web server port (default 8000)")

    args = parser.parse_args()

    if args.test:
        import pytest
        sys.exit(pytest.main(["-v", "tests/"]))
    elif args.headless:
        run_headless_benchmark()
    else:
        start_web_server(args.port)


if __name__ == "__main__":
    main()
