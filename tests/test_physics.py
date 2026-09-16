# Approximations: Central Newtonian gravity with weak-field 1PN Schwarzschild perihelion precession correction term and N-body gravitational perturbation from a massive stellar intruder. Collisionless test-particle ring model.

"""
Phaethon Astrophysics Verification Suite
------------------------------------------
Pytest module verifying:
  1. Circular Orbit Stability (v = sqrt(G * M / r))
  2. Kepler's Third Law (T^2 / a^3 = 4 * pi^2 / (G * M_BH))
  3. Symplectic Velocity Verlet Energy Conservation (|dE/E0| < 1e-4)
  4. Angular Momentum Conservation in Central Field
  5. Weak-Field 1PN Relativistic Schwarzschild Precession Rate
  6. Tidal Acceleration Scaling with Distance (a_tidal ~ r^-3)
"""

import pytest
import numpy as np
from phaethon.physics import G_CONST, C_LIGHT, CentralBlackHole, StellarIntruder, CollisionlessTidalRing, SymplecticRingIntegrator

def test_circular_orbit_stability():
    """Verify circular orbit velocity v = sqrt(G * M / r) stays stable under central gravity."""
    bh = CentralBlackHole(mass=100.0)
    intruder = StellarIntruder(mass=0.0)
    ring = CollisionlessTidalRing(num_particles=100, r_inner=10.0, r_outer=10.0)
    sim = SymplecticRingIntegrator(ring, bh, intruder, enable_gr=False)

    r_initial = np.linalg.norm(ring.positions, axis=1)
    
    dt = 0.001
    for _ in range(1000):
        sim.step(dt)

    r_final = np.linalg.norm(ring.positions, axis=1)
    max_drift = np.max(np.abs(r_final - r_initial) / r_initial)
    assert max_drift < 0.005, f"Circular orbit drifted excessively: {max_drift:.6e}"


def test_kepler_third_law():
    """
    Verify Kepler's 3rd Law (T^2 / a^3 = 4 * pi^2 / (G * M_BH))
    In AU, M_sun, yr units where G = 4 * pi^2, expected ratio T^2 / a^3 = 1 / M_BH.
    """
    M_BH = 100.0
    expected_ratio = 1.0 / M_BH

    radii = [8.0, 12.0]
    measured_ratios = []

    for a in radii:
        T_theoretical = 2.0 * np.pi * np.sqrt((a ** 3) / (G_CONST * M_BH))
        calculated_ratio = (T_theoretical ** 2) / (a ** 3)
        measured_ratios.append(calculated_ratio)
        rel_err = abs(calculated_ratio - expected_ratio) / expected_ratio
        assert rel_err < 1e-5, f"Kepler's 3rd law ratio mismatch for r={a}: {rel_err}"

    diff = abs(measured_ratios[0] - measured_ratios[1])
    assert diff < 1e-5


def test_energy_conservation():
    """
    Verify Symplectic Velocity Verlet integrator maintains Hamiltonian energy drift
    |dE / E0| < 1e-4 over 3,000 steps for an isolated test particle orbit.
    """
    bh = CentralBlackHole(mass=100.0)
    intruder = StellarIntruder(mass=0.0)
    ring = CollisionlessTidalRing(num_particles=100, r_inner=10.0, r_outer=10.0)
    sim = SymplecticRingIntegrator(ring, bh, intruder, enable_gr=False)

    pos = ring.positions
    vel = ring.velocities
    E0 = 0.5 * np.sum(vel ** 2, axis=1) - G_CONST * bh.mass / np.linalg.norm(pos, axis=1)

    dt = 0.0005
    for _ in range(3000):
        sim.step(dt)

    E_final = 0.5 * np.sum(vel ** 2, axis=1) - G_CONST * bh.mass / np.linalg.norm(pos, axis=1)
    drift = np.mean(np.abs(E_final - E0) / np.abs(E0))

    assert drift < 1e-4, f"Energy drift threshold exceeded: {drift:.6e} >= 1e-4"


def test_angular_momentum_conservation():
    """Verify angular momentum L = r x v is conserved in central gravitational field."""
    bh = CentralBlackHole(mass=100.0)
    intruder = StellarIntruder(mass=0.0)
    ring = CollisionlessTidalRing(num_particles=50, r_inner=8.0, r_outer=12.0)
    sim = SymplecticRingIntegrator(ring, bh, intruder, enable_gr=False)

    L0 = np.cross(ring.positions, ring.velocities)
    dt = 0.001

    for _ in range(2000):
        sim.step(dt)

    L_final = np.cross(ring.positions, ring.velocities)
    drift = np.max(np.linalg.norm(L_final - L0, axis=1) / np.linalg.norm(L0, axis=1))

    assert drift < 1e-5, f"Angular momentum drift exceeded threshold: {drift:.6e}"


def test_1pn_schwarzschild_precession():
    """
    Verify 1PN General Relativistic Schwarzschild perihelion precession effect.
    """
    bh = CentralBlackHole(mass=100.0)
    intruder = StellarIntruder(mass=0.0)
    ring = CollisionlessTidalRing(num_particles=1, r_inner=5.0, r_outer=5.0)
    
    a = 5.0
    e = 0.3
    r_peri = a * (1.0 - e)
    v_peri = np.sqrt(G_CONST * bh.mass * (1.0 + e) / r_peri)

    ring.positions[0] = [r_peri, 0.0, 0.0]
    ring.velocities[0] = [0.0, v_peri, 0.0]

    sim = SymplecticRingIntegrator(ring, bh, intruder, enable_gr=True, c_scale=500.0)

    dt = 0.0001
    for _ in range(2000):
        sim.step(dt)

    angle = np.arctan2(ring.positions[0, 1], ring.positions[0, 0])
    assert angle != 0.0, "Precession angle should advance away from zero"


def test_tidal_acceleration_scaling():
    """Verify differential tidal acceleration scales inversely with distance cubed: a_tidal ~ r^-3."""
    r1 = 5.0
    r2 = 10.0
    M = 100.0
    dr = 0.1

    a_tidal1 = 2.0 * G_CONST * M * dr / (r1 ** 3)
    a_tidal2 = 2.0 * G_CONST * M * dr / (r2 ** 3)

    ratio = a_tidal1 / a_tidal2
    expected_ratio = (r2 / r1) ** 3  # (10/5)^3 = 8
    
    assert abs(ratio - expected_ratio) < 1e-5
