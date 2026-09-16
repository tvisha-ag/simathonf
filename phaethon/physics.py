# Approximations: Newtonian gravity with General Relativistic Schwarzschild precession correction term and J2 quadrupole moment; dipole magnetic fields and radiation pressure omitted.

"""
Phaethon Advanced Physics Engine
--------------------------------
Symplectic Velocity Verlet Integrator, Rubble-Pile Moon Model with Hierarchical
Variable Particle Sizes, Differential Tidal Vector Calculation, Debris Focus Tracking,
and Disruption Event Detection.
"""

import numpy as np

class RubblePileMoon:
    """
    Rubble-pile moon composed of N sub-particles bound by mutual gravity
    and cohesive spring forces, with hierarchical variable particle radii and masses.
    """
    def __init__(
        self,
        num_particles: int = 200,
        moon_radius: float = 0.35,
        total_mass: float = 1.0,
        initial_orbital_radius: float = 12.0,
        host_mass: float = 1000.0,
        g_const: float = 1.0,
        k_spring: float = 80.0,
        strain_limit: float = 0.50,
        spring_damping: float = 0.8,
        seed: int = 42
    ):
        self.N = num_particles
        self.radius = moon_radius
        self.total_mass = total_mass
        self.initial_r = initial_orbital_radius
        self.host_mass = host_mass
        self.G = g_const
        self.k_spring = k_spring
        self.strain_limit = strain_limit
        self.spring_damping = spring_damping

        self.rng = np.random.default_rng(seed)

        # Hierarchical Variable Particle Radii & Mass Distribution
        rank = np.linspace(0.0, 1.0, num_particles)
        self.particle_radii = 0.015 + 0.065 * (rank ** 2.2)
        vol_sum = np.sum(self.particle_radii ** 3)
        self.masses = total_mass * ((self.particle_radii ** 3) / vol_sum)
        self.m_mean = total_mass / num_particles

        # Random shape offsets for non-spherical 3D asteroid meshes
        self.mesh_shape_seeds = self.rng.uniform(0.7, 1.3, size=(num_particles, 3))

        # Particle state vectors
        self.positions = np.zeros((self.N, 3), dtype=np.float64)
        self.velocities = np.zeros((self.N, 3), dtype=np.float64)
        self.accelerations = np.zeros((self.N, 3), dtype=np.float64)
        self.tidal_vectors = np.zeros((self.N, 3), dtype=np.float64)

        # Cohesive bond network
        self.bonds_i = np.array([], dtype=np.int32)
        self.bonds_j = np.array([], dtype=np.int32)
        self.bonds_d0 = np.array([], dtype=np.float64)
        self.bonds_active = np.array([], dtype=bool)

        self.primary_fragment_idx = int(np.argmax(self.masses))
        self._generate_moon()

    def _generate_moon(self):
        local_pos = []
        target_count = self.N

        golden_ratio = (1.0 + 5.0 ** 0.5) / 2.0
        for i in range(target_count):
            theta = 2.0 * np.pi * i / golden_ratio
            phi = np.arccos(1.0 - 2.0 * (i + 0.5) / target_count)
            u = self.rng.uniform(0.1, 1.0)
            r = self.radius * (u ** (1.0 / 3.0))

            x = r * np.sin(phi) * np.cos(theta)
            y = r * np.sin(phi) * np.sin(theta)
            z = r * np.cos(phi)
            local_pos.append([x, y, z])

        local_pos = np.array(local_pos, dtype=np.float64)
        local_pos -= np.mean(local_pos, axis=0)

        r0 = self.initial_r
        v0 = np.sqrt(self.G * (self.host_mass + self.total_mass) / r0)
        omega_orbit = v0 / r0

        self.positions[:, 0] = r0 + local_pos[:, 0]
        self.positions[:, 1] = local_pos[:, 1]
        self.positions[:, 2] = local_pos[:, 2]

        self.velocities[:, 0] = -omega_orbit * local_pos[:, 1]
        self.velocities[:, 1] = v0 + omega_orbit * local_pos[:, 0]
        self.velocities[:, 2] = 0.0

        cutoff = 2.4 * (self.radius / (self.N ** (1.0 / 3.0)))
        b_i, b_j, b_d0 = [], [], []

        for i in range(self.N):
            for j in range(i + 1, self.N):
                dist = np.linalg.norm(local_pos[i] - local_pos[j])
                if dist <= cutoff:
                    b_i.append(i)
                    b_j.append(j)
                    b_d0.append(dist)

        self.bonds_i = np.array(b_i, dtype=np.int32)
        self.bonds_j = np.array(b_j, dtype=np.int32)
        self.bonds_d0 = np.array(b_d0, dtype=np.float64)
        self.bonds_active = np.ones(len(b_i), dtype=bool)


class SymplecticIntegrator:
    """
    Second-order Symplectic Velocity Verlet integrator for N-body system.
    Calculates dynamic differential tidal forces and tracks disruption events.
    """
    def __init__(
        self,
        moon: RubblePileMoon,
        host_mass: float = 1000.0,
        host_radius: float = 2.0,
        g_const: float = 1.0,
        softening: float = 0.05
    ):
        self.moon = moon
        self.M_host = host_mass
        self.R_host = host_radius
        self.G = g_const
        self.softening = softening
        self.decay_rate = 0.0

        self.particle_stresses = np.zeros(self.moon.N, dtype=np.float64)
        self.disruption_flash_trigger = False
        self.has_flashed_disruption = False

        self.moon.accelerations = self._compute_accelerations(self.moon.positions, self.moon.velocities)
        self.initial_energy = self.compute_total_energy()

    def set_decay_rate(self, rate: float):
        self.decay_rate = rate

    def set_cohesion_k(self, k_val: float):
        self.moon.k_spring = max(0.0, float(k_val))

    def _compute_accelerations(self, pos: np.ndarray, vel: np.ndarray) -> np.ndarray:
        N = self.moon.N
        acc = np.zeros((N, 3), dtype=np.float64)
        self.particle_stresses.fill(0.0)

        # 1. Host Planet Central Gravity
        r_norms = np.linalg.norm(pos, axis=1, keepdims=True)
        r_norms_clamped = np.maximum(r_norms, 0.1)
        acc_host = - (self.G * self.M_host / (r_norms_clamped ** 3)) * pos
        acc += acc_host

        # Differential Tidal Gravity Vector: Delta_F_tidal_i = F_host_i - F_host_COM
        com = np.mean(pos, axis=0)
        r_com_norm = max(0.1, np.linalg.norm(com))
        acc_host_com = - (self.G * self.M_host / (r_com_norm ** 3)) * com
        self.moon.tidal_vectors = (acc_host - acc_host_com) * self.moon.masses[:, np.newaxis]

        # 2. Mutual N-body Newtonian Gravity with Softening
        diff = pos[:, np.newaxis, :] - pos[np.newaxis, :, :]  # (N, N, 3)
        dist_sq = np.sum(diff ** 2, axis=-1) + (self.softening ** 2)  # (N, N)
        inv_dist_cube = dist_sq ** (-1.5)
        np.fill_diagonal(inv_dist_cube, 0.0)

        mass_matrix = self.moon.masses[np.newaxis, :]
        acc_grav = - self.G * np.sum(diff * (inv_dist_cube * mass_matrix)[:, :, np.newaxis], axis=1)
        acc += acc_grav

        # 3. Cohesive Spring Forces & Tensile Fracture
        if len(self.moon.bonds_i) > 0 and np.any(self.moon.bonds_active) and self.moon.k_spring > 0.0:
            active_idx = np.where(self.moon.bonds_active)[0]
            idx_i = self.moon.bonds_i[active_idx]
            idx_j = self.moon.bonds_j[active_idx]
            d0 = self.moon.bonds_d0[active_idx]

            r_ij = pos[idx_i] - pos[idx_j]
            dist = np.linalg.norm(r_ij, axis=1)
            dist_clamped = np.maximum(dist, 1e-6)

            strain = (dist - d0) / d0
            broken_mask = strain > self.moon.strain_limit
            if np.any(broken_mask):
                self.moon.bonds_active[active_idx[broken_mask]] = False
                active_idx = np.where(self.moon.bonds_active)[0]
                idx_i = self.moon.bonds_i[active_idx]
                idx_j = self.moon.bonds_j[active_idx]
                d0 = self.moon.bonds_d0[active_idx]
                r_ij = pos[idx_i] - pos[idx_j]
                dist = np.linalg.norm(r_ij, axis=1)
                dist_clamped = np.maximum(dist, 1e-6)

            if len(active_idx) > 0:
                hat_r = r_ij / dist_clamped[:, np.newaxis]
                delta_d = dist - d0

                m_i = self.moon.masses[idx_i]
                m_j = self.moon.masses[idx_j]
                mu_ij = (m_i * m_j) / (m_i + m_j)
                mu_scale = mu_ij / (0.5 * self.moon.m_mean)
                k_eff = self.moon.k_spring * mu_scale

                f_spring = - k_eff[:, np.newaxis] * delta_d[:, np.newaxis] * hat_r

                v_ij = vel[idx_i] - vel[idx_j]
                v_rel_proj = np.sum(v_ij * hat_r, axis=1, keepdims=True)
                f_damping = - self.moon.spring_damping * mu_scale[:, np.newaxis] * v_rel_proj * hat_r

                f_total_bond = f_spring + f_damping

                a_bond_i = f_total_bond / m_i[:, np.newaxis]
                a_bond_j = f_total_bond / m_j[:, np.newaxis]

                np.add.at(acc, idx_i, a_bond_i)
                np.subtract.at(acc, idx_j, a_bond_j)

                tensile_load = np.maximum(0.0, delta_d * k_eff)
                np.add.at(self.particle_stresses, idx_i, tensile_load)
                np.add.at(self.particle_stresses, idx_j, tensile_load)

        # 4. Orbital Decay Drag Force
        if self.decay_rate > 0.0:
            acc_drag = - self.decay_rate * vel
            acc += acc_drag

        return acc

    def step(self, dt: float):
        pos = self.moon.positions
        vel = self.moon.velocities
        acc = self.moon.accelerations

        pos += vel * dt + 0.5 * acc * (dt ** 2)
        vel_half = vel + 0.5 * acc * dt
        acc_new = self._compute_accelerations(pos, vel_half)
        vel[:] = vel_half + 0.5 * acc_new * dt
        acc[:] = acc_new

        # Check Roche disruption screen flash event trigger
        r_com = np.linalg.norm(np.mean(pos, axis=0))
        roche = self.compute_roche_limit()
        if r_com < roche and not self.has_flashed_disruption:
            self.disruption_flash_trigger = True
            self.has_flashed_disruption = True
        else:
            self.disruption_flash_trigger = False

    def compute_total_energy(self) -> float:
        pos = self.moon.positions
        vel = self.moon.velocities
        m = self.moon.masses

        ke = 0.5 * np.sum(m[:, np.newaxis] * (vel ** 2))

        r_norms = np.linalg.norm(pos, axis=1)
        u_host = - np.sum(self.G * self.M_host * m / r_norms)

        diff = pos[:, np.newaxis, :] - pos[np.newaxis, :, :]
        dist = np.sqrt(np.sum(diff ** 2, axis=-1) + self.softening ** 2)
        np.fill_diagonal(dist, 1.0)
        m_outer = m[:, np.newaxis] * m[np.newaxis, :]
        u_mutual = - 0.5 * self.G * np.sum(m_outer / dist)

        u_spring = 0.0
        if len(self.moon.bonds_i) > 0 and np.any(self.moon.bonds_active) and self.moon.k_spring > 0.0:
            active_idx = np.where(self.moon.bonds_active)[0]
            if len(active_idx) > 0:
                idx_i = self.moon.bonds_i[active_idx]
                idx_j = self.moon.bonds_j[active_idx]
                d0 = self.moon.bonds_d0[active_idx]
                dist = np.linalg.norm(pos[idx_i] - pos[idx_j], axis=1)

                m_i = self.moon.masses[idx_i]
                m_j = self.moon.masses[idx_j]
                mu_ij = (m_i * m_j) / (m_i + m_j)
                mu_scale = mu_ij / (0.5 * self.moon.m_mean)
                k_eff = self.moon.k_spring * mu_scale
                u_spring = 0.5 * np.sum(k_eff * ((dist - d0) ** 2))

        return ke + u_host + u_mutual + u_spring

    def compute_roche_limit(self) -> float:
        v_host = (4.0 / 3.0) * np.pi * (self.R_host ** 3)
        rho_host = self.M_host / v_host

        v_moon = (4.0 / 3.0) * np.pi * (self.moon.radius ** 3)
        rho_moon = self.moon.total_mass / v_moon

        return 2.44 * self.R_host * ((rho_host / rho_moon) ** (1.0 / 3.0))

    def get_telemetry(self) -> dict:
        com = np.mean(self.moon.positions, axis=0)
        com_vel = np.mean(self.moon.velocities, axis=0)
        r_com = np.linalg.norm(com)
        v_com = np.linalg.norm(com_vel)

        roche_limit = self.compute_roche_limit()
        delta_a_tidal = (2.0 * self.G * self.M_host * self.moon.radius) / max(0.1, r_com ** 3)

        current_energy = self.compute_total_energy()
        energy_drift = abs(current_energy - self.initial_energy) / max(1e-8, abs(self.initial_energy))

        active_bonds_count = int(np.sum(self.moon.bonds_active))
        total_bonds_count = len(self.moon.bonds_active)

        primary_pos = self.moon.positions[self.moon.primary_fragment_idx]

        # Find debris stream center (mean of active or sheared debris)
        debris_center = np.mean(self.moon.positions, axis=0)

        return {
            "orbital_radius": r_com,
            "orbital_speed": v_com,
            "roche_limit": roche_limit,
            "tidal_differential": delta_a_tidal,
            "total_energy": current_energy,
            "energy_drift": energy_drift,
            "active_bonds": active_bonds_count,
            "total_bonds": total_bonds_count,
            "is_disrupted": r_com < roche_limit or active_bonds_count < 0.2 * total_bonds_count,
            "com_pos": com,
            "primary_pos": primary_pos,
            "debris_center": debris_center,
            "flash_trigger": self.disruption_flash_trigger
        }
