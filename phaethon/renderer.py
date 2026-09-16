# Approximations: Pure Newtonian gravity (no GR correction), classical Hookean cohesion model, rigid host planet.

"""
Phaethon PyOpenGL & Pygame Visual Engine
----------------------------------------
Interactive 3D viewport, Skybox Star Catalogue System, lit Host Planet,
stress/velocity color-coded rubble-pile particles, cohesive bond lines,
Roche limit golden wireframe, orbital trails, and real-time telemetry HUD overlay.
"""

import sys
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from phaethon.star_catalog import StarCatalogSkybox
from phaethon.physics import SymplecticIntegrator

class Camera3D:
    def __init__(self):
        self.yaw = 45.0
        self.pitch = 25.0
        self.distance = 32.0
        self.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.is_dragging = False
        self.is_panning = False
        self.last_mouse = (0, 0)
        self.follow_moon = False

    def handle_event(self, event: pygame.event.Event):
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click rotate
                self.is_dragging = True
                self.last_mouse = event.pos
            elif event.button == 3:  # Right click pan
                self.is_panning = True
                self.last_mouse = event.pos
            elif event.button == 4:  # Wheel up zoom in
                self.distance = max(4.0, self.distance - 1.5)
            elif event.button == 5:  # Wheel down zoom out
                self.distance = min(150.0, self.distance + 1.5)

        elif event.type == MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging = False
            elif event.button == 3:
                self.is_panning = False

        elif event.type == MOUSEMOTION:
            dx = event.pos[0] - self.last_mouse[0]
            dy = event.pos[1] - self.last_mouse[1]
            self.last_mouse = event.pos

            if self.is_dragging:
                self.yaw += dx * 0.4
                self.pitch += dy * 0.4
                self.pitch = max(-88.0, min(88.0, self.pitch))
            elif self.is_panning:
                rad_yaw = np.radians(self.yaw)
                self.target[0] -= (dx * np.cos(rad_yaw) + dy * np.sin(rad_yaw)) * 0.05
                self.target[1] += (dx * np.sin(rad_yaw) - dy * np.cos(rad_yaw)) * 0.05

    def update_follow(self, moon_com: np.ndarray):
        if self.follow_moon:
            self.target = moon_com.astype(np.float32)

    def apply_transform(self):
        glLoadIdentity()
        rad_yaw = np.radians(self.yaw)
        rad_pitch = np.radians(self.pitch)

        cam_x = self.target[0] + self.distance * np.cos(rad_pitch) * np.sin(rad_yaw)
        cam_y = self.target[1] + self.distance * np.sin(rad_pitch)
        cam_z = self.target[2] + self.distance * np.cos(rad_pitch) * np.cos(rad_yaw)

        gluLookAt(
            cam_x, cam_y, cam_z,
            self.target[0], self.target[1], self.target[2],
            0.0, 1.0, 0.0
        )


class Renderer3D:
    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height
        self.camera = Camera3D()
        self.star_catalog = StarCatalogSkybox(sky_radius=600.0)

        self.color_mode = "STRESS"  # "STRESS" or "VELOCITY"
        self.show_bonds = True
        self.show_roche = True
        self.show_stars = True

        self.hud_font = None
        self.hud_font_bold = None

        self._init_opengl()
        self._init_fonts()
        self._build_sphere_display_list()

    def _init_opengl(self):
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, self.width / float(self.height), 0.1, 1500.0)
        glMatrixMode(GL_MODELVIEW)

        glClearColor(0.02, 0.02, 0.05, 1.0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

        # Enable anti-aliasing for points and lines
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        # Blending setup
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Lighting setup for Host Planet
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        glLightfv(GL_LIGHT0, GL_POSITION, [15.0, 20.0, 25.0, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.95, 0.85, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.15, 0.15, 0.2, 1.0])

    def _init_fonts(self):
        pygame.font.init()
        try:
            self.hud_font = pygame.font.SysFont("Consolas", 15)
            self.hud_font_bold = pygame.font.SysFont("Consolas", 18, bold=True)
        except Exception:
            self.hud_font = pygame.font.Font(None, 18)
            self.hud_font_bold = pygame.font.Font(None, 22)

    def _build_sphere_display_list(self):
        """Build OpenGL display list for fast low-poly sphere rendering."""
        self.sphere_list = glGenLists(1)
        glNewList(self.sphere_list, GL_COMPILE)
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        gluSphere(quadric, 1.0, 24, 24)
        gluDeleteQuadric(quadric)
        glEndList()

    def resize(self, width: int, height: int):
        self.width = max(1, width)
        self.height = max(1, height)
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, self.width / float(self.height), 0.1, 1500.0)
        glMatrixMode(GL_MODELVIEW)

    def render_skybox(self):
        """Render astronomical skybox star catalog background."""
        if not self.show_stars:
            return

        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)

        # Draw 1,000 real astronomical catalog stars
        glPointSize(2.5)
        glBegin(GL_POINTS)
        for i in range(len(self.star_catalog.positions)):
            pos = self.star_catalog.positions[i]
            col = self.star_catalog.colors[i]
            glColor3f(col[0], col[1], col[2])
            glVertex3f(pos[0], pos[1], pos[2])
        glEnd()

        glEnable(GL_DEPTH_TEST)
        glDepthMask(GL_TRUE)

    def render_host_planet(self, radius: float = 2.0):
        """Render glowing textured host planet centered at origin."""
        glEnable(GL_LIGHTING)
        glPushMatrix()
        glLoadMatrixf(glGetFloatv(GL_MODELVIEW_MATRIX))

        # Host Planet base color (Mars ochre / terracotta)
        glColor3f(0.85, 0.42, 0.22)
        glScalef(radius, radius, radius)
        glCallList(self.sphere_list)

        glPopMatrix()

        # Render atmospheric glow rim
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive blending for glow

        glPushMatrix()
        glColor4f(0.95, 0.55, 0.25, 0.18)
        glScalef(radius * 1.12, radius * 1.12, radius * 1.12)
        glCallList(self.sphere_list)
        glPopMatrix()

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def render_roche_limit(self, roche_radius: float):
        """Render theoretical Roche Limit boundary wireframe sphere & equatorial ring."""
        if not self.show_roche:
            return

        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        # Equatorial ring line
        glColor4f(1.0, 0.85, 0.2, 0.6)
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        segments = 90
        for i in range(segments):
            theta = 2.0 * np.pi * i / segments
            x = roche_radius * np.cos(theta)
            z = roche_radius * np.sin(theta)
            glVertex3f(x, 0.0, z)
        glEnd()

        # Semi-transparent wireframe sphere
        glColor4f(1.0, 0.75, 0.1, 0.08)
        quadric = gluNewQuadric()
        gluQuadricDrawStyle(quadric, GLU_LINE)
        glPushMatrix()
        glRotatef(90, 1, 0, 0)
        gluSphere(quadric, roche_radius, 16, 16)
        glPopMatrix()
        gluDeleteQuadric(quadric)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def render_moon_particles(self, sim: SymplecticIntegrator):
        """Render rubble-pile sub-particles with stress/velocity color coding."""
        moon = sim.moon
        pos = moon.positions
        vel = moon.velocities
        stresses = sim.particle_stresses

        glDisable(GL_LIGHTING)

        # 1. Render Active Cohesive Spring Bonds
        if self.show_bonds and len(moon.bonds_i) > 0:
            active_idx = np.where(moon.bonds_active)[0]
            if len(active_idx) > 0:
                idx_i = moon.bonds_i[active_idx]
                idx_j = moon.bonds_j[active_idx]
                d0 = moon.bonds_d0[active_idx]
                dists = np.linalg.norm(pos[idx_i] - pos[idx_j], axis=1)
                strains = np.maximum(0.0, (dists - d0) / d0)

                glLineWidth(1.2)
                glBegin(GL_LINES)
                for k in range(len(active_idx)):
                    st = min(1.0, strains[k] / moon.strain_limit)
                    # Color transition: Cyan/Green (low strain) -> Yellow -> Red/Magenta (near snap)
                    r = float(st)
                    g = float(1.0 - 0.7 * st)
                    b = float(1.0 - st)
                    glColor4f(r, g, b, 0.4 + 0.4 * st)

                    p1 = pos[idx_i[k]]
                    p2 = pos[idx_j[k]]
                    glVertex3f(p1[0], p1[1], p1[2])
                    glVertex3f(p2[0], p2[1], p2[2])
                glEnd()

        # 2. Render Sub-Particles as Glowing Spheres / Point Sprites
        glEnable(GL_LIGHTING)
        v_norms = np.linalg.norm(vel, axis=1)
        max_v = np.max(v_norms) + 1e-5
        min_v = np.min(v_norms)

        max_s = np.max(stresses) + 1e-5

        particle_radius = moon.radius / (moon.N ** (1.0 / 3.0)) * 0.75

        for i in range(moon.N):
            glPushMatrix()
            glTranslatef(pos[i, 0], pos[i, 1], pos[i, 2])
            glScalef(particle_radius, particle_radius, particle_radius)

            if self.color_mode == "STRESS":
                # Gravitational Stress Mode: Blue -> Yellow -> Magenta/Red
                s_norm = min(1.0, stresses[i] / max(50.0, max_s))
                r = float(min(1.0, 2.0 * s_norm))
                g = float(min(1.0, 2.0 * (1.0 - s_norm)))
                b = float(max(0.1, 1.0 - s_norm * 1.5))
                glColor3f(r, g, b)
            else:
                # Velocity Magnitude Mode: Cyan (slow outer) -> Green -> Red (fast inner)
                v_norm = (v_norms[i] - min_v) / (max_v - min_v + 1e-6)
                r = float(v_norm)
                g = float(1.0 - abs(v_norm - 0.5) * 2.0)
                b = float(1.0 - v_norm)
                glColor3f(r, g, b)

            glCallList(self.sphere_list)
            glPopMatrix()

    def render_hud(self, sim: SymplecticIntegrator, fps: float, paused: bool, time_val: float, decay_on: bool):
        """Render crisp 2D orthographic Telemetry HUD overlay."""
        telem = sim.get_telemetry()

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # HUD Overlay Banner Lines
        status_str = "DISRUPTIVE TIDAL SHEAR!" if telem["is_disrupted"] else "STABLE ORBIT"
        status_color = (255, 60, 90) if telem["is_disrupted"] else (60, 240, 150)

        lines = [
            ("PHAETHON: ROCHE LIMIT & TIDAL DISRUPTION ENGINE", (255, 215, 0), True),
            ("Approximations: Pure Newtonian gravity (no GR correction), classical Hookean cohesion model, rigid host planet.", (180, 190, 210), False),
            ("-----------------------------------------------------------------------------------------", (100, 120, 150), False),
            (f"Simulation Time: {time_val:.3f} s | FPS: {fps:.1f} | Status: {status_str}", status_color, True),
            (f"Orbital Radius (r):       {telem['orbital_radius']:8.3f} AU | Roche Limit (r_Roche): {telem['roche_limit']:8.3f} AU", (240, 240, 255), False),
            (f"Tidal Differential (Δa):  {telem['tidal_differential']:8.4f}    | Active Cohesive Bonds:  {telem['active_bonds']:4d} / {telem['total_bonds']:4d}", (240, 240, 255), False),
            (f"Total Energy Drift (|ΔE|): {telem['energy_drift']:8.3e}   | Integrator: Symplectic Velocity Verlet", (240, 240, 255), False),
            (f"Color Mode: {self.color_mode} (Press 'C' to toggle) | Orbital Decay: {'ON' if decay_on else 'OFF'} (Press 'D')", (220, 220, 100), False),
        ]

        y_offset = 12
        for text, color, is_bold in lines:
            font = self.hud_font_bold if is_bold else self.hud_font
            surf = font.render(text, True, color)
            w, h = surf.get_size()

            text_data = pygame.image.tostring(surf, "RGBA", True)

            # Draw subtle dark background bar for readability
            glColor4f(0.05, 0.05, 0.1, 0.6)
            glBegin(GL_QUADS)
            glVertex2f(10, y_offset - 2)
            glVertex2f(10 + w + 8, y_offset - 2)
            glVertex2f(10 + w + 8, y_offset + h + 2)
            glVertex2f(10, y_offset + h + 2)
            glEnd()

            # Render text texture
            glRasterPos2f(14, y_offset + h)
            glDrawPixels(w, h, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

            y_offset += h + 4

        # Render Controls Legend at screen bottom
        legend_text = "[Space] Pause/Play | [D] Toggle Decay | [C] Color Mode | [R] Reset | [1-4] Camera Views | Mouse Drag/Scroll to Rotate/Zoom"
        legend_surf = self.hud_font.render(legend_text, True, (200, 200, 200))
        lw, lh = legend_surf.get_size()
        legend_data = pygame.image.tostring(legend_surf, "RGBA", True)

        glColor4f(0.05, 0.05, 0.1, 0.7)
        glBegin(GL_QUADS)
        glVertex2f(10, self.height - lh - 12)
        glVertex2f(10 + lw + 8, self.height - lh - 12)
        glVertex2f(10 + lw + 8, self.height - 4)
        glVertex2f(10, self.height - 4)
        glEnd()

        glRasterPos2f(14, self.height - 8)
        glDrawPixels(lw, lh, GL_RGBA, GL_UNSIGNED_BYTE, legend_data)

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glEnable(GL_DEPTH_TEST)
