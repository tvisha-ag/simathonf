# Phaethon: Relativistic Tidal Ring Disruption & Spacetime Engine
**Simathon Competition Edition — NASA APOD / Schnittman / Hubble TDE Cinematic Engine**

[![Physics Tests](https://img.shields.io/badge/Physics_Suite-9%2F9_Passed-00f0ff.svg)](#verification-suite)
[![Visual References](https://img.shields.io/badge/Visual_References-NASA_Schnittman_|_Hubble_TDE-ffd700.svg)](#cinematic-rendering)
[![License](https://img.shields.io/badge/License-MIT-gold.svg)](#license)

---

## 1. Project Overview

**Phaethon** is an interactive, physically defensible WebGL and Python astrophysics simulation built for scientific visualization and creative coding competitions.

Inspired directly by official **NASA Goddard (Jeremy Schnittman), NASA APOD, and Hubble Space Telescope TDE** visualizations, the application models the **tidal disruption of a thin icy particle ring** ($r_{\text{in}} = 5.5\,\text{AU}$, $r_{\text{out}} = 13.5\,\text{AU}$, vertical dispersion $\sigma_z = 0.05\,\text{AU}$) orbiting a Stellar-Mass Central Black Hole ($M_{\text{BH}} = 100\,M_\odot$) when perturbed by an eccentric, inclined Stellar Intruder ($M_{\text{star}} = 25\,M_\odot$).

Phaethon calculates differential gravitational forces across $15,000$ collisionless test particles using a 2nd-order **Symplectic Velocity Verlet** numerical integrator with optional **1PN Schwarzschild Post-Newtonian relativistic precession**, a live **Reference Orbit Overlay (`V` key)**, and a **3D Tidal Distortion Field** vector overlay.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    5-STAGE ASTROPHYSICAL TIMELINE                       │
│ 01 ORDERED RING → 02 INTRUDER APPROACH → 03 CLOSE ENCOUNTER           │
│                  → 04 TIDAL RESPONSE → 05 DEBRIS EVOLUTION             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Cinematic Shader Architecture (NASA GSFC & Hubble TDE Inspired)

### A. Schnittman Relativistic Accretion Disk GLSL Shader
- **Event Horizon Shadow**: Pure pitch-black event horizon sphere ($r = 1.4\,\text{AU}$).
- **Incandescent Photon Ring**: Razor-thin brilliant rim ($r = 1.41\text{--}1.48\,\text{AU}$).
- **Doppler Beaming & Lensing Arches**: Custom WebGL fragment shader (`accretionShaderMat`) rendering:
  - Relativistic Doppler beaming asymmetry (approaching left side boosted white-hot/gold at $2.0\times$ intensity; receding right side dimmed deep crimson).
  - Gravitational lensing arches (upper and lower warped disk overlays folded over top and under bottom of the event horizon, matching NASA Schnittman ray-tracing models).
  - Concentric thermal ringlets and dynamic GLSL turbulence noise.

### B. Procedural Stellar Plasma Shader (Stellar Intruder Body)
- Replaces primitive spheres with a custom GLSL stellar surface shader (`stellarShaderMat`):
  - Procedural 3D noise simulating stellar surface convection cells (granulation / turbulent plasma motion).
  - Limb brightening transition from incandescent white core to solar flare amber edges.
  - Soft volumetric atmospheric solar corona layer overlay.

### C. Volumetric TDE Plasma Stream Ribbon Mesh (`tdeStreamShaderMat`)
- Implements a dynamic WebGL ribbon mesh along the centroid arc of tidally disrupted particles.
- Renders a white-hot plasma core ($T > 10,000\,\text{K}$) with glowing golden/red plasma edges and additive blending, turning the tidal disruption event into a continuous streaming plasma ribbon matching NASA Hubble TDE visualizations.

### D. Procedural B-V Multi-Temperature Deep Space Starfield
- Renders 5,000 deep-space stars mapped according to real astronomical B-V temperature colors (hot blue O/B stars `#88c8ff`, solar yellow G stars `#fff4cc`, cool red M dwarfs `#ff9977`).

---

## 3. Physical Model & Equations

### Unit System & Constants
- **Length**: Astronomical Units ($\text{AU}$)
- **Mass**: Solar Masses ($M_\odot$)
- **Time**: Years ($\text{yr}$)
- **Gravitational Constant**: $G = 4\pi^2 \approx 39.47841760435743\;\text{AU}^3\,M_\odot^{-1}\,\text{yr}^{-2}$

### Gravitational Acceleration
$$\mathbf{a}_i = -\frac{G M_{\text{BH}} \mathbf{r}_i}{|\mathbf{r}_i|^3} - \frac{G M_{\text{star}} (\mathbf{r}_i - \mathbf{r}_{\text{star}})}{\left(|\mathbf{r}_i - \mathbf{r}_{\text{star}}|^2 + \epsilon^2\right)^{3/2}} + \mathbf{a}_{\text{1PN}}$$

where $M_{\text{BH}} = 100\,M_\odot$, $M_{\text{star}} = 25\,M_\odot$, and $\epsilon = 0.15\;\text{AU}$ (Plummer softening).

### Weak-Field 1PN Relativistic Precession (`RELATIVITY: ON/OFF`)
$$\mathbf{a}_{\text{1PN}} = -\frac{3 G M_{\text{BH}} L_i^2}{c_{\text{eff}}^2 r_i^5} \mathbf{r}_i \quad \text{where } \mathbf{L}_i = \mathbf{r}_i \times \mathbf{v}_i$$

---

## 4. Continuous Physical Color Mapping

Particle colors carry direct physical meaning based on orbital energy perturbation relative to their initial circular Keplerian state ($\text{Dev}_i = |E_i(t) - E_{i,0}| / |E_{i,0}|$):

| Perturbation $\text{Dev}_i$ | Color | Physical Meaning |
|---|---|---|
| $< 0.05$ | **Ice Cyan / Blue-White** (`#d0f0ff`) | Stable / Unperturbed Keplerian Orbit |
| $0.05 \le \text{Dev}_i < 0.20$ | **Stellar Gold** (`#ffd700`) | Moderately Perturbed / Density Wave |
| $0.20 \le \text{Dev}_i < 0.50$ | **Incandescent Crimson** (`#ff3010`) | Strongly Perturbed / Tidal Stream |
| $\ge 0.50$ | **White-Hot Plasma** (`#ffffff`) | High-Energy Escaping Debris |

---

## 5. Distinction Between Physical Layers & Approximations

1. **Collisionless Icy Ring (Simulated Test Particles)**:
   - Cool cyan/gold/crimson particle sprites representing collisionless debris orbiting in the black hole's gravitational potential.
2. **Accretion Disk & Lensing Arches (Optically Thick Emission Layer)**:
   - Procedural WebGL GLSL shader layer representing thermal gas accretion emission lensed by General Relativistic spacetime bending around the event horizon.
3. **Approximations & Scope**:
   - Gravitational lensing is computed using high-resolution GLSL shader warping rather than offline 3D GR geodesic ray tracing.
   - Relativistic precession uses 1PN Schwarzschild weak-field expansion.

---

## 6. Quick Start & Execution

### Launch WebGL Observatory (Primary Deliverable)
```bash
python main.py
```
*(Serves WebGL simulation at `http://localhost:8000` with strict no-cache headers)*

### Run Headless Energy Conservation Benchmark
```bash
python main.py --headless
```

### Run Autonomous Physics Verification Suite
```bash
python -m pytest -v tests/
```

---

## 7. Keybindings & Controls

| Key / Input | Action |
|---|---|
| **`SPACE`** | Pause / Resume simulation |
| **`R`** | Reset ring & intruder to initial state |
| **`V`** | Toggle Reference Orbit Outline Loops |
| **`T`** | Toggle 3D Tidal Distortion Vector Field |
| **`G`** | Toggle 1PN Relativistic Schwarzschild Precession |
| **`W`** / **`UP`** | Increase simulation speed ($+0.5\times$) |
| **`S`** / **`DOWN`** | Decrease simulation speed ($-0.5\times$) |
| **`ESC`** | Reset camera view |
| **Mouse Drag** | Arcball orbit camera rotation |
| **Mouse Scroll** | Camera zoom in / out |

---

## 8. Verification Suite Results

All 9 automated physics unit tests pass cleanly:

```
============================= test session starts =============================
tests/test_physics.py::test_circular_orbit_stability PASSED              [ 11%]
tests/test_physics.py::test_kepler_third_law PASSED                      [ 22%]
tests/test_physics.py::test_energy_conservation PASSED                   [ 33%]
tests/test_physics.py::test_angular_momentum_conservation PASSED         [ 44%]
tests/test_physics.py::test_1pn_schwarzschild_precession PASSED          [ 55%]
tests/test_physics.py::test_tidal_acceleration_scaling PASSED            [ 66%]
tests/test_simulation.py::test_star_catalog_temperature_and_rgb PASSED   [ 77%]
tests/test_simulation.py::test_simulation_app_lifecycle PASSED           [ 88%]
tests/test_simulation.py::test_stellar_intruder_trajectory PASSED        [100%]

============================== 9 passed in 2.73s ==============================
```

---

## 9. License

Licensed under the MIT License.
