# Approximations: Pure Newtonian gravity (no GR correction), classical Hookean cohesion model, rigid host planet.

"""
Phaethon Simulation Controller Module
---------------------------------------
Orchestrates physics integrator sub-stepping, time control, orbital decay,
camera tracking, and state reset.
"""

import numpy as np
from phaethon.physics import RubblePileMoon, SymplecticIntegrator

class SimulationApp:
    def __init__(
        self,
        num_particles: int = 200,
        initial_radius: float = 12.0,
        decay_rate: float = 0.006,
        dt: float = 0.002
    ):
        self.num_particles = num_particles
        self.initial_radius = initial_radius
        self.default_decay_rate = decay_rate
        self.dt = dt

        self.paused = False
        self.decay_on = False
        self.simulation_time = 0.0
        self.step_count = 0

        self.moon = None
        self.integrator = None
        self.reset()

    def reset(self):
        """Reset physics simulation state to initial orbit outside Roche limit."""
        self.moon = RubblePileMoon(
            num_particles=self.num_particles,
            moon_radius=0.35,
            total_mass=1.0,
            initial_orbital_radius=self.initial_radius,
            host_mass=1000.0,
            g_const=1.0,
            k_spring=80.0,
            strain_limit=0.50,
            spring_damping=0.8,
            seed=42
        )
        self.integrator = SymplecticIntegrator(
            moon=self.moon,
            host_mass=1000.0,
            host_radius=2.0,
            g_const=1.0,
            softening=0.05
        )
        if self.decay_on:
            self.integrator.set_decay_rate(self.default_decay_rate)
        else:
            self.integrator.set_decay_rate(0.0)

        self.simulation_time = 0.0
        self.step_count = 0

    def toggle_pause(self):
        self.paused = not self.paused

    def toggle_decay(self):
        self.decay_on = not self.decay_on
        if self.decay_on:
            self.integrator.set_decay_rate(self.default_decay_rate)
        else:
            self.integrator.set_decay_rate(0.0)

    def update(self, sub_steps: int = 4):
        """Advance physics state by multiple sub-steps for maximum stability."""
        if self.paused:
            return

        for _ in range(sub_steps):
            self.integrator.step(self.dt)
            self.simulation_time += self.dt
            self.step_count += 1
