# Approximations: Central Newtonian gravity with weak-field 1PN Schwarzschild perihelion precession correction term and N-body gravitational perturbation from a massive stellar intruder. Collisionless test-particle ring model.

"""
Phaethon Simulation Controller Module
---------------------------------------
Orchestrates collisionless tidal ring physics sub-stepping, time control,
stellar intruder trajectory, and state reset.
"""

import numpy as np
from phaethon.physics import CentralBlackHole, StellarIntruder, CollisionlessTidalRing, SymplecticRingIntegrator

class SimulationApp:
    def __init__(
        self,
        num_particles: int = 5000,
        r_inner: float = 6.0,
        r_outer: float = 14.0,
        dt: float = 0.002,
        enable_gr: bool = True
    ):
        self.num_particles = num_particles
        self.r_inner = r_inner
        self.r_outer = r_outer
        self.dt = dt
        self.enable_gr = enable_gr

        self.paused = False
        self.simulation_speed = 1.0
        self.simulation_time = 0.0
        self.step_count = 0

        self.bh = None
        self.intruder = None
        self.ring = None
        self.integrator = None
        self.reset()

    def reset(self):
        """Reset physics simulation state to initial pristine ring + intruder at apocenter."""
        self.bh = CentralBlackHole(mass=100.0, radius=0.5)
        self.intruder = StellarIntruder(
            mass=15.0,
            pericenter=4.0,
            eccentricity=0.85,
            inclination_deg=25.0,
            central_mass=100.0
        )
        self.ring = CollisionlessTidalRing(
            num_particles=self.num_particles,
            r_inner=self.r_inner,
            r_outer=self.r_outer,
            thickness=0.15,
            central_mass=100.0,
            seed=42
        )
        self.integrator = SymplecticRingIntegrator(
            ring=self.ring,
            black_hole=self.bh,
            intruder=self.intruder,
            enable_gr=self.enable_gr
        )

        self.simulation_time = 0.0
        self.step_count = 0

    def toggle_pause(self):
        self.paused = not self.paused

    def toggle_gr(self):
        self.enable_gr = not self.enable_gr
        if self.integrator:
            self.integrator.enable_gr = self.enable_gr

    def set_speed(self, factor: float):
        self.simulation_speed = max(0.1, min(5.0, factor))

    def update(self, sub_steps: int = 4):
        """Advance physics state by multiple sub-steps for maximum stability."""
        if self.paused:
            return

        effective_dt = self.dt * self.simulation_speed
        for _ in range(sub_steps):
            self.integrator.step(effective_dt / sub_steps)
            self.simulation_time += effective_dt / sub_steps
            self.step_count += 1
