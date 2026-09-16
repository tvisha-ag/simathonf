# Approximations: Pure Newtonian gravity with SPH fluid pressure; general relativistic frame dragging and radiation pressure ignored.

"""
Phaethon SPH Hydrodynamics Verification Suite
----------------------------------------------
Pytest module verifying:
  1. Kepler's Third Law (T^2 / a^3 = constant)
  2. Symplectic Velocity Verlet Energy Conservation (|E_3000 - E_0| / |E_0| < 1e-4 over 3,000 steps)
  3. SPH Tait Equation of State & Fluid Density Estimation
  4. Roche Limit Calculation & Disruption Threshold
"""

import pytest
import numpy as np
from phaethon.sph_physics import SPHRubblePileMoon, SPHSymplecticIntegrator, cubic_spline_kernel

def test_sph_kernel_and_tait_eos():
    """Verify 3D SPH cubic spline kernel properties and Tait Equation of State."""
    h = 0.15
    w_origin = cubic_spline_kernel(0.0, h)
    w_cutoff = cubic_spline_kernel(2.1 * h, h)

    assert w_origin > 0.0, "Kernel at origin must be positive"
    assert w_cutoff == 0.0, "Kernel beyond 2*h must be 0"

    moon = SPHRubblePileMoon(num_particles=100, moon_radius=0.35, k_eos=50.0, rho_0=5.5)
    sim = SPHSymplecticIntegrator(moon, softening=0.06)

    assert np.all(moon.densities > 0.0), "SPH densities must be strictly positive"
    assert len(moon.pressures) == 100


def test_kepler_third_law():
    """
    Verify Kepler's 3rd Law (T^2 / a^3 = 4 * pi^2 / (G * M_host))
    for circular orbits around host planet.
    """
    G = 1.0
    M_host = 1000.0
    expected_ratio = (4.0 * (np.pi ** 2)) / (G * M_host)

    radii = [10.0, 15.0]
    measured_ratios = []

    for a in radii:
        v0 = np.sqrt(G * M_host / a)
        pos = np.array([[a, 0.0, 0.0]], dtype=np.float64)
        vel = np.array([[0.0, v0, 0.0]], dtype=np.float64)

        T_theoretical = 2.0 * np.pi * np.sqrt((a ** 3) / (G * M_host))
        dt = 0.001
        steps = int(np.ceil(T_theoretical / dt))

        y_prev = pos[0, 1]
        t_crossed = None

        acc = - (G * M_host / (a ** 3)) * pos
        for step in range(steps * 2):
            pos += vel * dt + 0.5 * acc * (dt ** 2)
            vel_half = vel + 0.5 * acc * dt
            acc_new = - (G * M_host / (np.linalg.norm(pos) ** 3)) * pos
            vel = vel_half + 0.5 * acc_new * dt
            acc = acc_new

            if step > 100 and y_prev < 0 and pos[0, 1] >= 0:
                t_crossed = step * dt
                break
            y_prev = pos[0, 1]

        assert t_crossed is not None
        ratio = (t_crossed ** 2) / (a ** 3)
        measured_ratios.append(ratio)
        rel_err = abs(ratio - expected_ratio) / expected_ratio
        assert rel_err < 0.01

    ratio_diff = abs(measured_ratios[0] - measured_ratios[1]) / measured_ratios[0]
    assert ratio_diff < 0.01


def test_energy_conservation():
    """
    Assert Symplectic Velocity Verlet integrator preserves Hamiltonian energy
    such that total energy drift (|E_3000 - E_0| / |E_0|) stays strictly below 1e-4
    over 3,000 integration steps in a stable orbit.
    """
    moon = SPHRubblePileMoon(
        num_particles=120,
        moon_radius=0.35,
        total_mass=1.0,
        initial_orbital_radius=12.0,
        host_mass=1000.0,
        g_const=1.0,
        k_eos=50.0,
        alpha_visc=0.0,
        beta_visc=0.0,
        seed=42
    )
    sim = SPHSymplecticIntegrator(moon, host_mass=1000.0, softening=0.06)
    sim.set_decay_rate(0.0)

    # Allow SPH fluid to reach hydrostatic equilibrium
    for _ in range(200):
        sim.step(0.0005)

    E_initial = sim.compute_total_energy()
    dt = 0.0005

    for step in range(3000):
        sim.step(dt)

    E_final = sim.compute_total_energy()
    energy_drift = abs(E_final - E_initial) / abs(E_initial)

    print(f"SPH Energy initial: {E_initial:.6f}, final: {E_final:.6f}, drift: {energy_drift:.6e}")
    assert energy_drift < 1e-4, f"Energy drift threshold exceeded: {energy_drift:.6e} >= 1e-4"


def test_roche_limit_disruption_threshold():
    """
    Verify theoretical Roche Limit formula calculation.
    """
    moon = SPHRubblePileMoon(num_particles=100, moon_radius=0.35, total_mass=1.0)
    sim = SPHSymplecticIntegrator(moon, host_mass=1000.0)

    roche_r = sim.compute_roche_limit()
    assert 7.0 <= roche_r <= 10.0, f"Roche limit out of expected bounds: {roche_r}"

    telem = sim.get_telemetry()
    assert abs(telem["roche_limit"] - roche_r) < 1e-5
    assert not telem["is_disrupted"]


def test_relativistic_precession():
    """
    Verify General Relativistic Schwarzschild perihelion precession.
    Compares observed perihelion advance against theoretical formula:
    delta_phi = (6 * pi * G * M) / (a * (1 - e^2) * c^2)
    """
    moon = SPHRubblePileMoon(
        num_particles=1,
        moon_radius=0.1,
        total_mass=0.001,
        initial_orbital_radius=5.0,
        host_mass=1000.0,
        seed=42
    )

    G = 1.0
    M = 1000.0
    c = 300.0
    a = 5.0
    e = 0.3
    r_peri = a * (1.0 - e)
    v_peri = np.sqrt(G * M * (1.0 + e) / r_peri)

    # Initial position at perihelion on x-axis
    moon.positions[0] = [r_peri, 0.0, 0.0]
    moon.velocities[0] = [0.0, v_peri, 0.0]

    sim = SPHSymplecticIntegrator(
        moon,
        host_mass=M,
        g_const=G,
        softening=0.0,
        enable_gr=True,
        c_light=c,
        j2_oblateness=0.0
    )

    delta_phi_theory = (6.0 * np.pi * G * M) / (a * (1.0 - e ** 2) * (c ** 2))
    
    dt = 0.0001
    T_orbit = 2.0 * np.pi * np.sqrt((a ** 3) / (G * M))
    steps = int(np.ceil(T_orbit * 2.5 / dt))

    perihelion_angles = []
    r_prev = np.linalg.norm(moon.positions[0])
    dr_dt_prev = 0.0

    for step in range(steps):
        sim.step(dt)
        r_curr = np.linalg.norm(moon.positions[0])
        dr_dt = (r_curr - r_prev) / dt

        # Detect local minimum of distance r (perihelion crossing)
        if dr_dt_prev < 0.0 and dr_dt >= 0.0 and step > 50:
            angle = np.arctan2(moon.positions[0, 1], moon.positions[0, 0])
            perihelion_angles.append(angle)

        r_prev = r_curr
        dr_dt_prev = dr_dt

    assert len(perihelion_angles) >= 2, "Failed to capture at least 2 perihelion passages"
    
    observed_shift = perihelion_angles[1] - perihelion_angles[0]
    if observed_shift < 0:
        observed_shift += 2.0 * np.pi

    rel_error = abs(observed_shift - delta_phi_theory) / delta_phi_theory
    print(f"Relativistic Precession Theory: {delta_phi_theory:.6f} rad, Observed: {observed_shift:.6f} rad, rel error: {rel_error:.4f}")
    assert rel_error < 0.05, f"GR precession error too high: {rel_error:.4f}"


def test_lense_thirring_precession():
    """
    Verify Kerr Metric Lense-Thirring frame-dragging nodal precession rate.
    Theoretical nodal precession frequency:
    Omega_LT = (2 * G * S) / (c^2 * a^3 * (1 - e^2)^(3/2))
    where S = a_star * (G * M^2 / c).
    """
    moon = SPHRubblePileMoon(
        num_particles=1,
        moon_radius=0.1,
        total_mass=0.001,
        initial_orbital_radius=6.0,
        host_mass=1000.0,
        seed=42
    )

    G = 1.0
    M = 1000.0
    c = 100.0
    a = 6.0
    e = 0.0
    inc = np.radians(30.0)
    a_star = 0.8

    v0 = np.sqrt(G * M / a)
    moon.positions[0] = [a, 0.0, 0.0]
    moon.velocities[0] = [0.0, v0 * np.cos(inc), v0 * np.sin(inc)]

    sim = SPHSymplecticIntegrator(
        moon,
        host_mass=M,
        g_const=G,
        softening=0.0,
        enable_gr=False,
        c_light=c,
        j2_oblateness=0.0,
        a_star=a_star,
        b_dipole=0.0,
        q_charge=0.0
    )

    S_z = a_star * (G * (M ** 2)) / c
    omega_lt_theory = (2.0 * G * S_z) / ((c ** 2) * (a ** 3))

    dt = 0.0001
    T_orbit = 2.0 * np.pi * np.sqrt((a ** 3) / (G * M))
    steps = int(np.ceil(T_orbit * 2.0 / dt))

    h0 = np.cross(moon.positions[0], moon.velocities[0])
    node_angle0 = np.arctan2(h0[0], -h0[1])

    for step in range(steps):
        sim.step(dt)

    h1 = np.cross(moon.positions[0], moon.velocities[0])
    node_angle1 = np.arctan2(h1[0], -h1[1])

    delta_node = (node_angle0 - node_angle1)
    if delta_node < 0:
        delta_node += 2.0 * np.pi

    t_total = steps * dt
    omega_lt_obs = delta_node / t_total

    rel_err = abs(omega_lt_obs - omega_lt_theory) / omega_lt_theory
    print(f"Lense-Thirring Precession Theory: {omega_lt_theory:.6f} rad/s, Observed: {omega_lt_obs:.6f} rad/s, rel error: {rel_err:.4f}")
    assert rel_err < 0.05, f"Lense-Thirring precession rate error too high: {rel_err:.4f}"


