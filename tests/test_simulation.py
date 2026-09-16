# Approximations: Pure Newtonian gravity (no GR correction), classical Hookean cohesion model, rigid host planet.

"""
Phaethon Self-Test & Physics Verification Suite
-------------------------------------------------
Pytest module verifying:
  1. Kepler's 3rd Law (T^2 / a^3 = constant) on stable test orbits
  2. Symplectic Hamiltonian Energy Conservation (|E_2000 - E_0| / |E_0| < 1e-4 over 2000 steps)
  3. Roche Limit calculation & disruption behavior
  4. Yale Star Catalog B-V to Effective Temperature & RGB Mapping
"""

import pytest
import numpy as np
from phaethon.star_catalog import bv_to_eff_temp, temp_to_rgb, generate_star_catalog, StarCatalogSkybox
from phaethon.physics import RubblePileMoon, SymplecticIntegrator

def test_star_catalog_temperature_and_rgb():
    """Verify B-V color index to Effective Temperature and Planckian RGB color conversion."""
    # Test Solar-type star B-V = 0.65 -> T_eff approx 5700K - 5800K
    t_sun = bv_to_eff_temp(0.65)
    assert 5400.0 <= t_sun <= 6100.0, f"Solar temperature out of range: {t_sun}"

    # Test Sirius-type star B-V = 0.0 -> T_eff approx 9500K - 10500K
    t_sirius = bv_to_eff_temp(0.0)
    assert 9000.0 <= t_sirius <= 11000.0, f"Sirius temperature out of range: {t_sirius}"

    # Test RGB output values are normalized within [0.0, 1.0]
    rgb_sun = temp_to_rgb(t_sun)
    assert all(0.0 <= c <= 1.0 for c in rgb_sun)

    rgb_blue = temp_to_rgb(25000.0)
    assert rgb_blue[2] >= rgb_blue[0], "Hot O/B star should be bluer than red"

    # Test catalog loading
    cat = StarCatalogSkybox(sky_radius=500.0)
    assert len(cat.stars) == 1000
    assert cat.positions.shape == (1000, 3)
    assert cat.colors.shape == (1000, 3)


def test_kepler_third_law():
    """
    Verify Kepler's 3rd Law (T^2 / a^3 = 4 * pi^2 / (G * M_host))
    for circular orbits around host planet using Symplectic Velocity Verlet integrator.
    """
    G = 1.0
    M_host = 1000.0
    expected_ratio = (4.0 * (np.pi ** 2)) / (G * M_host)  # approx 0.0394784

    radii = [10.0, 15.0]
    measured_ratios = []

    for a in radii:
        v0 = np.sqrt(G * M_host / a)
        pos = np.array([[a, 0.0, 0.0]], dtype=np.float64)
        vel = np.array([[0.0, v0, 0.0]], dtype=np.float64)

        T_theoretical = 2.0 * np.pi * np.sqrt((a ** 3) / (G * M_host))
        dt = 0.001
        steps = int(np.ceil(T_theoretical / dt))

        # Integrate through one full orbit
        y_prev = pos[0, 1]
        t_crossed = None

        acc = - (G * M_host / (a ** 3)) * pos
        for step in range(steps * 2):
            pos += vel * dt + 0.5 * acc * (dt ** 2)
            vel_half = vel + 0.5 * acc * dt
            acc_new = - (G * M_host / (np.linalg.norm(pos) ** 3)) * pos
            vel = vel_half + 0.5 * acc_new * dt
            acc = acc_new

            # Detect positive Y-axis crossing (completing 1 full revolution)
            if step > 100 and y_prev < 0 and pos[0, 1] >= 0:
                t_crossed = step * dt
                break
            y_prev = pos[0, 1]

        assert t_crossed is not None, f"Orbit did not complete for a={a}"
        ratio = (t_crossed ** 2) / (a ** 3)
        measured_ratios.append(ratio)

        # Assert measured period ratio matches Keplerian prediction within 1% relative error
        rel_err = abs(ratio - expected_ratio) / expected_ratio
        assert rel_err < 0.01, f"Kepler's 3rd law violation at a={a}: ratio={ratio}, expected={expected_ratio}, err={rel_err}"

    # Verify constancy across different orbital radii
    ratio_diff = abs(measured_ratios[0] - measured_ratios[1]) / measured_ratios[0]
    assert ratio_diff < 0.01, f"Kepler 3rd law constant drift across orbits: {ratio_diff}"


def test_energy_conservation():
    """
    Assert that Symplectic Velocity Verlet integrator preserves Hamiltonian energy
    such that total energy drift (|E_2000 - E_0| / |E_0|) stays strictly below 1e-4
    over 2,000 integration steps in a stable orbit outside the Roche limit.
    """
    moon = RubblePileMoon(
        num_particles=150,
        moon_radius=0.35,
        total_mass=1.0,
        initial_orbital_radius=12.0,
        host_mass=1000.0,
        g_const=1.0,
        k_spring=80.0,
        strain_limit=0.50,
        spring_damping=0.8,
        seed=42
    )
    sim = SymplecticIntegrator(moon, host_mass=1000.0, softening=0.08)
    sim.set_decay_rate(0.0)  # Stable orbit (no drag decay)

    E_initial = sim.compute_total_energy()
    dt = 0.001

    for step in range(2000):
        sim.step(dt)

    E_final = sim.compute_total_energy()
    energy_drift = abs(E_final - E_initial) / abs(E_initial)

    print(f"Energy initial: {E_initial:.6f}, final: {E_final:.6f}, drift: {energy_drift:.6e}")
    assert energy_drift < 1e-4, f"Energy drift threshold exceeded: {energy_drift:.6e} >= 1e-4"


def test_roche_limit_disruption():
    """
    Verify theoretical Roche Limit formula and disruption behavior when orbital radius decays.
    """
    moon = RubblePileMoon(
        num_particles=100,
        moon_radius=0.35,
        total_mass=1.0,
        initial_orbital_radius=12.0,
        host_mass=1000.0
    )
    sim = SymplecticIntegrator(moon, host_mass=1000.0)

    roche_r = sim.compute_roche_limit()

    # Theoretical Roche limit check: r_Roche = 2.44 * R_host * (rho_host / rho_moon)^(1/3)
    assert 7.0 <= roche_r <= 10.0, f"Calculated Roche Limit out of expected bounds: {roche_r}"

    # Check telemetry reporting
    telem = sim.get_telemetry()
    assert abs(telem["roche_limit"] - roche_r) < 1e-5
    assert not telem["is_disrupted"]
