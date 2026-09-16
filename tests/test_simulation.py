# Approximations: Central Newtonian gravity with weak-field 1PN Schwarzschild perihelion precession correction term and N-body gravitational perturbation from a massive stellar intruder. Collisionless test-particle ring model.

"""
Phaethon Self-Test & Simulation Verification Suite
---------------------------------------------------
Pytest module verifying:
  1. Yale Star Catalog B-V to Effective Temperature & RGB Mapping
  2. SimulationApp Lifecycle & Sub-Stepping Physics
  3. Stellar Intruder Orbit & Trajectory Integration
"""

import pytest
import numpy as np
from phaethon.star_catalog import bv_to_eff_temp, temp_to_rgb, generate_star_catalog, StarCatalogSkybox
from phaethon.physics import G_CONST, CentralBlackHole, StellarIntruder, CollisionlessTidalRing, SymplecticRingIntegrator
from phaethon.simulation import SimulationApp

def test_star_catalog_temperature_and_rgb():
    """Verify B-V color index to Effective Temperature and Planckian RGB color conversion."""
    t_sun = bv_to_eff_temp(0.65)
    assert 5400.0 <= t_sun <= 6100.0, f"Solar temperature out of range: {t_sun}"

    t_sirius = bv_to_eff_temp(0.0)
    assert 9000.0 <= t_sirius <= 11000.0, f"Sirius temperature out of range: {t_sirius}"

    rgb_sun = temp_to_rgb(t_sun)
    assert all(0.0 <= c <= 1.0 for c in rgb_sun)

    rgb_blue = temp_to_rgb(25000.0)
    assert rgb_blue[2] >= rgb_blue[0], "Hot O/B star should be bluer than red"

    cat = StarCatalogSkybox(sky_radius=500.0)
    assert len(cat.stars) == 1000
    assert cat.positions.shape == (1000, 3)
    assert cat.colors.shape == (1000, 3)


def test_simulation_app_lifecycle():
    """Verify SimulationApp initialization, pause, reset, and physics update steps."""
    app = SimulationApp(num_particles=500, dt=0.002, enable_gr=True)
    assert app.ring.N == 500
    assert app.simulation_time == 0.0

    app.update(sub_steps=4)
    assert app.simulation_time > 0.0
    assert app.step_count == 4

    app.toggle_pause()
    t_paused = app.simulation_time
    app.update(sub_steps=4)
    assert app.simulation_time == t_paused, "Simulation time should not advance while paused"

    app.toggle_pause()
    app.reset()
    assert app.simulation_time == 0.0, "Reset should restore simulation time to 0"


def test_stellar_intruder_trajectory():
    """Verify stellar intruder eccentric orbit integration around central black hole."""
    bh = CentralBlackHole(mass=100.0)
    intruder = StellarIntruder(mass=15.0, pericenter=4.0, eccentricity=0.85, central_mass=100.0)
    ring = CollisionlessTidalRing(num_particles=10, r_inner=8.0, r_outer=10.0)
    sim = SymplecticRingIntegrator(ring, bh, intruder, enable_gr=False)

    r_initial = np.linalg.norm(intruder.position)
    dt = 0.002

    # Step through orbit to approach pericenter
    min_r = r_initial
    for _ in range(5000):
        sim.step(dt)
        r_curr = np.linalg.norm(intruder.position)
        if r_curr < min_r:
            min_r = r_curr

    assert min_r < r_initial, "Intruder should approach pericenter on eccentric orbit"
    assert min_r < 6.0, f"Intruder pericenter not reached: min_r = {min_r:.2f}"
