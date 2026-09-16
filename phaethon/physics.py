# Approximations: Central Newtonian gravity with weak-field 1PN Schwarzschild perihelion precession correction term and N-body gravitational perturbation from a massive stellar intruder. Collisionless test-particle ring model.

"""
Phaethon Astrophysics Engine: Collisionless Tidal Ring & Relativistic Disruption
=================================================================================
Units: Astronomical Units (AU), Solar Masses (M_sun), Years (yr).
In these units, G = 4 * pi^2 approx 39.47841760435743.
Speed of light c = 63239.7 AU/yr.
"""

import numpy as np

# Fundamental Astronomical Constants (AU, M_sun, yr)
G_CONST = 4.0 * (np.pi ** 2)
C_LIGHT = 63239.7

class CentralBlackHole:
    """Central non-rotating Schwarzschild Black Hole."""
    def __init__(self, mass: float = 100.0, radius: float = 0.5):
        self.mass = mass
        self.radius = radius
        self.position = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        self.velocity = np.array([0.0, 0.0, 0.0], dtype=np.float64)


class StellarIntruder:
    """Massive stellar intruder following an eccentric, inclined Keplerian orbit."""
    def __init__(
        self,
        mass: float = 15.0,
        pericenter: float = 4.0,
        eccentricity: float = 0.85,
        inclination_deg: float = 25.0,
        central_mass: float = 100.0
    ):
        self.mass = mass
        self.pericenter = pericenter
        self.eccentricity = eccentricity
        self.inclination = np.radians(inclination_deg)
        self.central_mass = central_mass
        
        # Orbital parameters
        self.a = pericenter / (1.0 - eccentricity)
        self.period = 2.0 * np.pi * np.sqrt((self.a ** 3) / (G_CONST * (central_mass + mass)))
        
        self.position = np.zeros(3, dtype=np.float64)
        self.velocity = np.zeros(3, dtype=np.float64)
        
        # Initialize at apocenter
        self.reset()

    def reset(self):
        r_apo = self.a * (1.0 + self.eccentricity)
        v_apo = np.sqrt(G_CONST * (self.central_mass + self.mass) * (2.0 / r_apo - 1.0 / self.a))
        
        # Un-inclined coordinates at apocenter (along +X, moving in +Y)
        x0 = r_apo
        y0 = 0.0
        vx0 = 0.0
        vy0 = -v_apo
        
        # Rotate by inclination around X axis
        cos_i = np.cos(self.inclination)
        sin_i = np.sin(self.inclination)
        
        self.position[0] = x0
        self.position[1] = y0 * cos_i
        self.position[2] = y0 * sin_i
        
        self.velocity[0] = vx0
        self.velocity[1] = vy0 * cos_i
        self.velocity[2] = vy0 * sin_i


class CollisionlessTidalRing:
    """
    Pristine, multi-band ring of collisionless icy test particles
    orbiting a central black hole, perturbed by a massive stellar intruder.
    """
    def __init__(
        self,
        num_particles: int = 5000,
        r_inner: float = 6.0,
        r_outer: float = 14.0,
        thickness: float = 0.15,
        central_mass: float = 100.0,
        seed: int = 42
    ):
        self.N = num_particles
        self.r_inner = r_inner
        self.r_outer = r_outer
        self.thickness = thickness
        self.central_mass = central_mass
        self.rng = np.random.default_rng(seed)

        self.positions = np.zeros((self.N, 3), dtype=np.float64)
        self.velocities = np.zeros((self.N, 3), dtype=np.float64)
        self.initial_energies = np.zeros(self.N, dtype=np.float64)
        self.energy_perturbations = np.zeros(self.N, dtype=np.float64)
        self.tidal_accelerations = np.zeros(self.N, dtype=np.float64)
        
        self._generate_ring()

    def _generate_ring(self):
        # Generate multi-band radial density distribution
        u = self.rng.uniform(0.0, 1.0, self.N)
        radii = self.r_inner + (self.r_outer - self.r_inner) * np.sqrt(u)
        
        # Add subtle ringlet gap variations
        ringlet_mask = (radii > 9.0) & (radii < 9.6)
        radii[ringlet_mask] += self.rng.uniform(-0.4, 0.4, np.sum(ringlet_mask))
        
        angles = self.rng.uniform(0.0, 2.0 * np.pi, self.N)
        z_offsets = self.rng.normal(0.0, self.thickness, self.N)

        self.positions[:, 0] = radii * np.cos(angles)
        self.positions[:, 1] = radii * np.sin(angles)
        self.positions[:, 2] = z_offsets

        # Circular Keplerian orbital velocities v = sqrt(G * M / r)
        v_circ = np.sqrt(G_CONST * self.central_mass / radii)
        self.velocities[:, 0] = -v_circ * np.sin(angles)
        self.velocities[:, 1] = v_circ * np.cos(angles)
        self.velocities[:, 2] = 0.0

        # Initial specific orbital energy E0 = - G M / (2 a)
        self.initial_energies = - G_CONST * self.central_mass / (2.0 * radii)


class SymplecticRingIntegrator:
    """
    Second-Order Symplectic Velocity Verlet integrator for test-particle ring
    under central black hole and moving stellar intruder gravity.
    """
    def __init__(
        self,
        ring: CollisionlessTidalRing,
        black_hole: CentralBlackHole,
        intruder: StellarIntruder,
        enable_gr: bool = True,
        c_scale: float = 1000.0,
        softening: float = 0.15
    ):
        self.ring = ring
        self.bh = black_hole
        self.intruder = intruder
        self.enable_gr = enable_gr
        self.c_scale = c_scale
        self.softening = softening
        self.time = 0.0

        self.accelerations = self._compute_accelerations(
            self.ring.positions,
            self.ring.velocities,
            self.intruder.position
        )

    def _compute_intruder_acceleration(self, pos_intruder: np.ndarray, pos_bh: np.ndarray) -> np.ndarray:
        r_vec = pos_intruder - pos_bh
        r = np.linalg.norm(r_vec)
        r_clamped = max(0.1, r)
        return - (G_CONST * self.bh.mass / (r_clamped ** 3)) * r_vec

    def _compute_accelerations(self, pos: np.ndarray, vel: np.ndarray, pos_intruder: np.ndarray) -> np.ndarray:
        # 1. Central Black Hole Newtonian Gravity
        r_sq = np.sum(pos ** 2, axis=1, keepdims=True)
        r_norms = np.sqrt(r_sq)
        r_clamped = np.maximum(r_norms, 0.1)
        
        acc = - (G_CONST * self.bh.mass / (r_clamped ** 3)) * pos

        # 2. Stellar Intruder Gravity (Softened)
        diff_int = pos - pos_intruder  # (N, 3)
        dist_int_sq = np.sum(diff_int ** 2, axis=1, keepdims=True) + (self.softening ** 2)
        dist_int_cube = dist_int_sq ** 1.5
        acc_int = - (G_CONST * self.intruder.mass / dist_int_cube) * diff_int
        acc += acc_int

        # Track tidal acceleration magnitude near intruder
        self.ring.tidal_accelerations = np.linalg.norm(acc_int, axis=1)

        # 3. Weak-Field 1PN General Relativistic Schwarzschild Precession (Optional)
        if self.enable_gr:
            L_vecs = np.cross(pos, vel)  # (N, 3)
            L_sq = np.sum(L_vecs ** 2, axis=1, keepdims=True)  # (N, 1)
            c_effective = self.c_scale
            acc_1pn = - (3.0 * G_CONST * self.bh.mass * L_sq / ((c_effective ** 2) * (r_clamped ** 5))) * pos
            acc += acc_1pn

        return acc

    def step(self, dt: float):
        pos = self.ring.positions
        vel = self.ring.velocities
        acc = self.accelerations

        # 1. Intruder step (Velocity Verlet)
        acc_int = self._compute_intruder_acceleration(self.intruder.position, self.bh.position)
        self.intruder.position += self.intruder.velocity * dt + 0.5 * acc_int * (dt ** 2)
        vel_int_half = self.intruder.velocity + 0.5 * acc_int * dt
        acc_int_new = self._compute_intruder_acceleration(self.intruder.position, self.bh.position)
        self.intruder.velocity = vel_int_half + 0.5 * acc_int_new * dt

        # 2. Ring particle step (Symplectic Velocity Verlet)
        pos += vel * dt + 0.5 * acc * (dt ** 2)
        vel_half = vel + 0.5 * acc * dt

        acc_new = self._compute_accelerations(pos, vel_half, self.intruder.position)

        vel[:] = vel_half + 0.5 * acc_new * dt
        acc[:] = acc_new

        self.time += dt
        self._update_telemetry()

    def _update_telemetry(self):
        # Compute specific orbital energy E = 0.5 * v^2 - G * M_BH / r
        pos = self.ring.positions
        vel = self.ring.velocities
        r_norms = np.linalg.norm(pos, axis=1)
        current_energies = 0.5 * np.sum(vel ** 2, axis=1) - G_CONST * self.bh.mass / r_norms
        
        # Energy perturbation ratio |E - E0| / |E0|
        self.ring.energy_perturbations = np.abs(current_energies - self.ring.initial_energies) / np.abs(self.ring.initial_energies)

    def get_telemetry(self) -> dict:
        intruder_dist = np.linalg.norm(self.intruder.position)
        perturbed_count = int(np.sum(self.ring.energy_perturbations > 0.08))
        max_tidal_acc = float(np.max(self.ring.tidal_accelerations))
        
        return {
            "simulation_time": self.time,
            "particle_count": self.ring.N,
            "black_hole_mass": self.bh.mass,
            "intruder_mass": self.intruder.mass,
            "intruder_distance": intruder_dist,
            "max_tidal_acc": max_tidal_acc,
            "perturbed_particles": perturbed_count,
            "gr_enabled": self.enable_gr,
            "intruder_pos": self.intruder.position.copy(),
            "intruder_vel": self.intruder.velocity.copy()
        }
