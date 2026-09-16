# Phaethon: Relativistic Tidal Disruption & Dynamic Ring Engine

> **Approximations**: Newtonian gravity with General Relativistic Schwarzschild precession correction term and J2 quadrupole moment; dipole magnetic fields and radiation pressure omitted.

**Phaethon** is a production-grade, AAA-quality WebGL2 / WebGPU interactive scientific simulation featuring General Relativistic (Schwarzschild) perihelion precession, $J_2$ quadrupole oblateness forces, Smoothed Particle Hydrodynamics (SPH), Symplectic Velocity Verlet integration, skybox gravitational lensing shaders, volumetric Rayleigh/Mie atmospheric scattering, thermal blackbody particle instancing, Three.js UnrealBloom post-processing, and a futuristic sci-fi glassmorphic telemetry dashboard.

---

## Technical Architecture & Physics Engine

```
+------------------------------------------------------------------------------------+
|               SYMPLECTIC VELOCITY VERLET INTEGRATOR (dt = 0.0015)                  |
+----------------------------------------+-------------------------------------------+
                                         |
     +-----------------------------------+-----------------------------------+
     |                                   |                                   |
+----v--------------------+    +---------v------------------+    +-----------v---------------+
| Central Newtonian & GR  |    | Host J2 Quadrupole Force   |    | SPH Tensile Strain & Heat |
| a_GR = -3GML^2/(c^2 r^5)|    | a_J2(r, z)                 |    | T = T_base + alpha*tensor |
+-------------------------+    +----------------------------+    +---------------------------+
```

1. **Symplectic Velocity Verlet Integrator**:
   - Preserves phase-space volume and maintains strict Hamiltonian energy conservation ($|E_{3000} - E_0|/|E_0| < 10^{-4}$) over 3,000 integration steps.
2. **General Relativistic (Schwarzschild) Perihelion Precession**:
   - Radial acceleration correction:
     $$\mathbf{a}_{\text{GR}} = -\frac{3 G M L^2}{c^2 r^5} \mathbf{r}$$
     Where $L = |\mathbf{r} \times \mathbf{v}|$ is specific angular momentum magnitude. Matches theoretical perihelion advance:
     $$\Delta \phi = \frac{6 \pi G M}{a (1 - e^2) c^2}$$
3. **$J_2$ Quadrupole Oblateness Force**:
   - Account for planetary rotational oblateness:
     $$\mathbf{a}_{J_2} = -\frac{3 G M J_2 R_{\text{host}}^2}{2 r^5} \left[ \left(1 - 5 \frac{z^2}{r^2}\right) \mathbf{r} + 2 z \hat{\mathbf{z}} \right]$$
4. **Smoothed Particle Hydrodynamics (SPH) & Tidal Stress Model**:
   - Differential tidal stress tensor norm $\|T_{ij}\| = \sqrt{6} G M / r^3$ converted to thermal heating ($T_i = 270\text{K} + \alpha \|T_{ij}\| + \text{strain}$).
   - Breakup fragments execute Keplerian shear orbits ($\omega = \sqrt{GM/r^3}$), forming dynamic multi-layered planetary rings.

---

## Graphical & GLSL Shader Pipeline

- **Atmospheric Raymarching PBR Planet Shader**: Volumetric Rayleigh ($\propto \lambda^{-4}$) and Mie scattering limb glow, cloud layer rotation, specular ocean reflections, and night-side city illuminations.
- **Gravitational Lensing Skybox Shader**: Deflects incoming view rays by $\alpha = \frac{4 G M}{c^2 b}$ toward origin, warping Yale Bright Star Catalog coordinates into dynamic Einstein rings around the primary mass.
- **Volumetric Thermal Instanced Particles**: Particles transition dynamically in color based on calculated internal stress (Dark Grey $\rightarrow$ Incandescent Crimson $\rightarrow$ Hot Gold $\rightarrow$ White-Blue).
- **Post-Processing Pipeline**: `EffectComposer`, `UnrealBloomPass` for thermal emissions, and chromatic aberration shader pass.

---

## Sci-Fi Glassmorphism HUD & Controls

- **Futuristic Control Dashboard**:
  - **Sliders**: Particle Count ($N = 500 - 5,000$), SPH Tensile Cohesion ($k$), Orbital Decay Rate, $J_2$ Oblateness.
  - **Toggles**: Relativistic Precession ON/OFF, Gravitational Lensing ON/OFF.
  - **Camera Target Lock Selector**: "Cinematic Orbital Arc", "Center of Mass Tracker", "Tidal Fragment Lock", "Host Mass View".
- **Telemetry Gauges**:
  - Live Mechanical Energy Conservation Graph ($|dE/E_0|$ vs Timestep canvas).
  - Real-Time Tidal Stress Tensor Heatmap Gauge (Green = Stable, Yellow = Deforming, Red = Rupture).
  - Distance to Roche Limit Bar + Telemetry Counter.

---

## Verification Suite

```bash
# 1. Run physics verification test suite (5 tests: Kepler 3rd Law, Energy Drift < 1e-4, GR Precession, SPH EOS, Roche Limit)
python -m pytest -v tests/test_physics.py

# 2. Launch interactive WebGL browser app
python main.py --web
```
