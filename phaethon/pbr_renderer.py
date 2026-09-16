# Approximations: Pure Newtonian gravity (no GR correction), classical Hookean cohesion model, rigid host planet.

"""
Phaethon NASA-Grade Modern GLSL Shader Renderer
-----------------------------------------------
Physically Based Rendering (PBR) Host Planet, 3D Non-Spherical Asteroid Meshes,
Live Tidal Stress Differential Force Vectors (3D Arrows), Volumetric Pulsating
Roche Limit Equipotential Shell, Screen Flash Event Trigger, Arcball Camera,
and Post-Processing.
"""

import sys
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

from phaethon.star_catalog import StarCatalogSkybox
from phaethon.physics import SymplecticIntegrator
from phaethon.shaders import (
    PLANET_VS, PLANET_FS,
    ASTEROID_VS, ASTEROID_FS,
    PARTICLE_VS, PARTICLE_FS,
    SKYBOX_STAR_VS, SKYBOX_STAR_FS,
    VECTOR_VS, VECTOR_FS,
    ROCHE_SHELL_VS, ROCHE_SHELL_FS
)

class ArcballCamera:
    """
    360-Degree Arcball Orbit Camera with Inertia, Tilt, Pan, Zoom,
    and Target Tracking Locks ("PLANET", "MOON", "PRIMARY", "DEBRIS").
    """
    def __init__(self):
        self.yaw = 45.0
        self.pitch = 25.0
        self.distance = 32.0
        self.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)

        self.vel_yaw = 0.0
        self.vel_pitch = 0.0
        self.vel_zoom = 0.0

        self.is_dragging = False
        self.is_panning = False
        self.last_mouse = (0, 0)

        # Tracking mode: "PLANET", "MOON", "PRIMARY", "DEBRIS"
        self.track_mode = "PLANET"

    def handle_event(self, event: pygame.event.Event):
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                self.is_dragging = True
                self.last_mouse = event.pos
                self.vel_yaw = 0.0
                self.vel_pitch = 0.0
            elif event.button == 3:
                self.is_panning = True
                self.last_mouse = event.pos
            elif event.button == 4:
                self.vel_zoom -= 1.2
            elif event.button == 5:
                self.vel_zoom += 1.2

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
                self.vel_yaw = dx * 0.35
                self.vel_pitch = dy * 0.35
            elif self.is_panning:
                rad_yaw = np.radians(self.yaw)
                self.target[0] -= (dx * np.cos(rad_yaw) + dy * np.sin(rad_yaw)) * 0.04
                self.target[1] += (dx * np.sin(rad_yaw) - dy * np.cos(rad_yaw)) * 0.04

    def update(self, dt: float, telem: dict):
        if self.track_mode == "MOON":
            self.target = telem["com_pos"].astype(np.float32)
        elif self.track_mode == "PRIMARY":
            self.target = telem["primary_pos"].astype(np.float32)
        elif self.track_mode == "DEBRIS":
            self.target = telem["debris_center"].astype(np.float32)
        elif self.track_mode == "PLANET":
            self.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)

        self.yaw += self.vel_yaw
        self.pitch += self.vel_pitch
        self.pitch = max(-89.0, min(89.0, self.pitch))

        self.distance += self.vel_zoom
        self.distance = max(3.0, min(180.0, self.distance))

        self.vel_yaw *= 0.88
        self.vel_pitch *= 0.88
        self.vel_zoom *= 0.80

    def get_eye_position(self) -> np.ndarray:
        rad_yaw = np.radians(self.yaw)
        rad_pitch = np.radians(self.pitch)
        cam_x = self.target[0] + self.distance * np.cos(rad_pitch) * np.sin(rad_yaw)
        cam_y = self.target[1] + self.distance * np.sin(rad_pitch)
        cam_z = self.target[2] + self.distance * np.cos(rad_pitch) * np.cos(rad_yaw)
        return np.array([cam_x, cam_y, cam_z], dtype=np.float32)

    def apply_transform(self):
        glLoadIdentity()
        eye = self.get_eye_position()
        gluLookAt(
            eye[0], eye[1], eye[2],
            self.target[0], self.target[1], self.target[2],
            0.0, 1.0, 0.0
        )


class PBRShaderRenderer:
    """
    Manages NASA-Grade GLSL Shaders, PBR Planet, Textured 3D Asteroids,
    Differential Tidal Force Vector Field, Pulsating Roche Shell, and Screen Flash Event.
    """
    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height
        self.camera = ArcballCamera()
        self.star_catalog = StarCatalogSkybox(sky_radius=600.0)

        self.color_mode = 0  # 0 = Stress, 1 = Velocity
        self.show_bonds = True
        self.show_roche = True
        self.show_stars = True
        self.show_vectors = True  # Toggle live Tidal Stress Vector Field
        self.show_asteroid_meshes = True

        self.time_val = 0.0
        self.flash_alpha = 0.0

        self._init_opengl()
        self._compile_shaders()
        self._build_geometry()

    def _init_opengl(self):
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, self.width / float(self.height), 0.1, 1800.0)
        glMatrixMode(GL_MODELVIEW)

        glClearColor(0.01, 0.01, 0.03, 1.0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

        glEnable(GL_PROGRAM_POINT_SIZE)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def _compile_shader_program(self, vs_src: str, fs_src: str) -> int:
        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, vs_src)
        glCompileShader(vs)
        if not glGetShaderiv(vs, GL_COMPILE_STATUS):
            err = glGetShaderInfoLog(vs).decode()
            raise RuntimeError(f"Vertex Shader Compile Error: {err}")

        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, fs_src)
        glCompileShader(fs)
        if not glGetShaderiv(fs, GL_COMPILE_STATUS):
            err = glGetShaderInfoLog(fs).decode()
            raise RuntimeError(f"Fragment Shader Compile Error: {err}")

        prog = glCreateProgram()
        glAttachShader(prog, vs)
        glAttachShader(prog, fs)
        glLinkProgram(prog)
        if not glGetProgramiv(prog, GL_LINK_STATUS):
            err = glGetProgramInfoLog(prog).decode()
            raise RuntimeError(f"Shader Link Error: {err}")

        return prog

    def _compile_shaders(self):
        self.planet_prog = self._compile_shader_program(PLANET_VS, PLANET_FS)
        self.asteroid_prog = self._compile_shader_program(ASTEROID_VS, ASTEROID_FS)
        self.particle_prog = self._compile_shader_program(PARTICLE_VS, PARTICLE_FS)
        self.star_prog = self._compile_shader_program(SKYBOX_STAR_VS, SKYBOX_STAR_FS)
        self.vector_prog = self._compile_shader_program(VECTOR_VS, VECTOR_FS)
        self.roche_prog = self._compile_shader_program(ROCHE_SHELL_VS, ROCHE_SHELL_FS)

    def _build_geometry(self):
        # Build sphere quadric list for host planet & Roche shell
        self.sphere_list = glGenLists(1)
        glNewList(self.sphere_list, GL_COMPILE)
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        gluQuadricTexture(quadric, GL_TRUE)
        gluSphere(quadric, 1.0, 36, 36)
        gluDeleteQuadric(quadric)
        glEndList()

    def resize(self, width: int, height: int):
        self.width = max(1, width)
        self.height = max(1, height)
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, self.width / float(self.height), 0.1, 1800.0)
        glMatrixMode(GL_MODELVIEW)

    def trigger_disruption_flash(self):
        self.flash_alpha = 0.85

    def render_skybox(self):
        if not self.show_stars:
            return

        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)

        glUseProgram(self.star_prog)
        view_mat = glGetFloatv(GL_MODELVIEW_MATRIX)
        proj_mat = glGetFloatv(GL_PROJECTION_MATRIX)

        glUniformMatrix4fv(glGetUniformLocation(self.star_prog, "view"), 1, GL_FALSE, view_mat)
        glUniformMatrix4fv(glGetUniformLocation(self.star_prog, "projection"), 1, GL_FALSE, proj_mat)
        glUniform1f(glGetUniformLocation(self.star_prog, "time"), self.time_val)

        glBegin(GL_POINTS)
        for i in range(len(self.star_catalog.positions)):
            pos = self.star_catalog.positions[i]
            col = self.star_catalog.colors[i]
            sz = self.star_catalog.sizes[i]
            glVertexAttrib3f(1, col[0], col[1], col[2])
            glVertexAttrib1f(2, sz)
            glVertex3f(pos[0], pos[1], pos[2])
        glEnd()

        glUseProgram(0)
        glEnable(GL_DEPTH_TEST)
        glDepthMask(GL_TRUE)

    def render_pbr_planet(self, radius: float = 2.0):
        glUseProgram(self.planet_prog)

        model_mat = np.eye(4, dtype=np.float32)
        model_mat[0, 0] = radius
        model_mat[1, 1] = radius
        model_mat[2, 2] = radius

        view_mat = glGetFloatv(GL_MODELVIEW_MATRIX)
        proj_mat = glGetFloatv(GL_PROJECTION_MATRIX)
        eye = self.camera.get_eye_position()

        glUniformMatrix4fv(glGetUniformLocation(self.planet_prog, "model"), 1, GL_FALSE, model_mat)
        glUniformMatrix4fv(glGetUniformLocation(self.planet_prog, "view"), 1, GL_FALSE, view_mat)
        glUniformMatrix4fv(glGetUniformLocation(self.planet_prog, "projection"), 1, GL_FALSE, proj_mat)
        glUniform3f(glGetUniformLocation(self.planet_prog, "lightDir"), 15.0, 20.0, 25.0)
        glUniform3f(glGetUniformLocation(self.planet_prog, "camPos"), eye[0], eye[1], eye[2])
        glUniform1f(glGetUniformLocation(self.planet_prog, "time"), self.time_val)

        glCallList(self.sphere_list)
        glUseProgram(0)

    def render_roche_equipotential_shell(self, roche_radius: float):
        if not self.show_roche:
            return

        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        glUseProgram(self.roche_prog)
        model_mat = np.eye(4, dtype=np.float32)
        model_mat[0, 0] = roche_radius
        model_mat[1, 1] = roche_radius
        model_mat[2, 2] = roche_radius

        view_mat = glGetFloatv(GL_MODELVIEW_MATRIX)
        proj_mat = glGetFloatv(GL_PROJECTION_MATRIX)

        glUniformMatrix4fv(glGetUniformLocation(self.roche_prog, "model"), 1, GL_FALSE, model_mat)
        glUniformMatrix4fv(glGetUniformLocation(self.roche_prog, "view"), 1, GL_FALSE, view_mat)
        glUniformMatrix4fv(glGetUniformLocation(self.roche_prog, "projection"), 1, GL_FALSE, proj_mat)
        glUniform1f(glGetUniformLocation(self.roche_prog, "time"), self.time_val)

        glCallList(self.sphere_list)
        glUseProgram(0)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def render_tidal_vector_field(self, sim: SymplecticIntegrator):
        """Render Live Tidal Stress Differential Force Vector Field (3D Force Arrows)."""
        if not self.show_vectors:
            return

        pos = sim.moon.positions
        t_vecs = sim.moon.tidal_vectors

        glUseProgram(self.vector_prog)
        view_mat = glGetFloatv(GL_MODELVIEW_MATRIX)
        proj_mat = glGetFloatv(GL_PROJECTION_MATRIX)

        glUniformMatrix4fv(glGetUniformLocation(self.vector_prog, "view"), 1, GL_FALSE, view_mat)
        glUniformMatrix4fv(glGetUniformLocation(self.vector_prog, "projection"), 1, GL_FALSE, proj_mat)

        glLineWidth(2.0)
        glBegin(GL_LINES)
        for i in range(0, sim.moon.N, 2):  # Sample sub-particles for clarity
            p = pos[i]
            v = t_vecs[i] * 350.0  # Vector length scaling
            v_norm = np.linalg.norm(v)

            # Color: Cyan for inward, Magenta/Red for outward tearing differential
            if v_norm > 0.1:
                col = (1.0, 0.2, 0.5, 0.85) if np.dot(v, p) > 0 else (0.1, 0.8, 1.0, 0.85)
                glVertexAttrib4f(1, col[0], col[1], col[2], col[3])
                glVertex3f(p[0], p[1], p[2])
                glVertex3f(p[0] + v[0], p[1] + v[1], p[2] + v[2])
        glEnd()

        glUseProgram(0)

    def render_thermal_particles_and_asteroids(self, sim: SymplecticIntegrator):
        moon = sim.moon
        pos = moon.positions
        vel = moon.velocities
        stresses = sim.particle_stresses
        radii = moon.particle_radii

        # 1. Render Cohesive Bonds if active
        if self.show_bonds and len(moon.bonds_i) > 0 and sim.moon.k_spring > 0.0:
            active_idx = np.where(moon.bonds_active)[0]
            if len(active_idx) > 0:
                idx_i = moon.bonds_i[active_idx]
                idx_j = moon.bonds_j[active_idx]
                d0 = moon.bonds_d0[active_idx]
                dists = np.linalg.norm(pos[idx_i] - pos[idx_j], axis=1)
                strains = np.maximum(0.0, (dists - d0) / d0)

                glDisable(GL_LIGHTING)
                glLineWidth(1.5)
                glBegin(GL_LINES)
                for k in range(len(active_idx)):
                    st = min(1.0, strains[k] / moon.strain_limit)
                    r = float(st)
                    g = float(1.0 - 0.7 * st)
                    b = float(1.0 - st)
                    glColor4f(r, g, b, 0.45 + 0.45 * st)

                    p1 = pos[idx_i[k]]
                    p2 = pos[idx_j[k]]
                    glVertex3f(p1[0], p1[1], p1[2])
                    glVertex3f(p2[0], p2[1], p2[2])
                glEnd()

        # 2. Render Non-Spherical 3D Asteroid Meshes & Volumetric Particles
        glUseProgram(self.asteroid_prog)

        view_mat = glGetFloatv(GL_MODELVIEW_MATRIX)
        proj_mat = glGetFloatv(GL_PROJECTION_MATRIX)
        eye = self.camera.get_eye_position()

        glUniformMatrix4fv(glGetUniformLocation(self.asteroid_prog, "view"), 1, GL_FALSE, view_mat)
        glUniformMatrix4fv(glGetUniformLocation(self.asteroid_prog, "projection"), 1, GL_FALSE, proj_mat)
        glUniform3f(glGetUniformLocation(self.asteroid_prog, "lightDir"), 15.0, 20.0, 25.0)
        glUniform3f(glGetUniformLocation(self.asteroid_prog, "camPos"), eye[0], eye[1], eye[2])
        glUniform1i(glGetUniformLocation(self.asteroid_prog, "colorMode"), self.color_mode)

        for i in range(moon.N):
            r = radii[i]
            # Render non-spherical 3D boulders
            glPushMatrix()
            glTranslatef(pos[i, 0], pos[i, 1], pos[i, 2])

            # Non-spherical distortion factor
            sx, sy, sz = moon.mesh_shape_seeds[i]
            glScalef(r * sx, r * sy, r * sz)

            glUniform1f(glGetUniformLocation(self.asteroid_prog, "stress"), float(stresses[i]))
            glCallList(self.sphere_list)
            glPopMatrix()

        glUseProgram(0)

        # 3. Volumetric Thermal Point-Sprite Dust Emission
        glUseProgram(self.particle_prog)

        model_mat = np.eye(4, dtype=np.float32)
        glUniformMatrix4fv(glGetUniformLocation(self.particle_prog, "model"), 1, GL_FALSE, model_mat)
        glUniformMatrix4fv(glGetUniformLocation(self.particle_prog, "view"), 1, GL_FALSE, view_mat)
        glUniformMatrix4fv(glGetUniformLocation(self.particle_prog, "projection"), 1, GL_FALSE, proj_mat)
        glUniform1i(glGetUniformLocation(self.particle_prog, "colorMode"), self.color_mode)
        glUniform1f(glGetUniformLocation(self.particle_prog, "time"), self.time_val)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        v_norms = np.linalg.norm(vel, axis=1)

        glBegin(GL_POINTS)
        for i in range(moon.N):
            glVertexAttrib1f(1, float(stresses[i]))
            glVertexAttrib1f(2, float(v_norms[i]))
            glVertexAttrib1f(3, float(radii[i]))
            glVertex3f(pos[i, 0], pos[i, 1], pos[i, 2])
        glEnd()

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glUseProgram(0)

    def render_disruption_screen_flash(self):
        """Render fullscreen white/orange flash overlay on Roche limit disruption crossing."""
        if self.flash_alpha <= 0.01:
            return

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glColor4f(1.0, 0.9, 0.7, self.flash_alpha)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(self.width, 0)
        glVertex2f(self.width, self.height)
        glVertex2f(0, self.height)
        glEnd()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Decay flash alpha over frames
        self.flash_alpha *= 0.85
