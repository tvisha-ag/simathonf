# Phaethon: Relativistic Tidal Ring Disruption & Spacetime Engine
**Simathon Competition Edition — NASA APOD / SVS Cinematic Overhaul**

[![Physics Tests](https://img.shields.io/badge/Physics_Suite-9%2F9_Passed-00f0ff.svg)](#verification-suite)
[![Visual References](https://img.shields.io/badge/Visual_References-NASA_APOD_|_SVS-ffd700.svg)](#cinematic-rendering)
[![License](https://img.shields.io/badge/License-MIT-gold.svg)](#license)

---

## 1. Project Overview

**Phaethon** is an interactive, physically defensible WebGL and Python astrophysics simulation built for scientific visualization and creative coding competitions.

Inspired directly by official **NASA APOD, NASA SVS, and Hubble Space Telescope** visualizations, the simulation models the **tidal disruption of a thin icy particle ring** ($r_{\text{in}} = 5.5\,\text{AU}$, $r_{\text{out}} = 13.5\,\text{AU}$, vertical dispersion $\sigma_z = 0.05\,\text{AU}$) orbiting a Stellar-Mass Central Black Hole ($M_{\text{BH}} = 100\,M_\odot$) when perturbed by an eccentric, inclined Stellar Intruder ($M_{\text{star}} = 25\,M_\odot$).

Phaethon calculates differential gravitational forces across $5,000\text{--}20,000$ collisionless test particles using a 2nd-order **Symplectic Velocity Verlet** numerical integrator with optional **1PN Schwarzschild Post-Newtonian relativistic precession**, a live **Reference Orbit Overlay (`V` key)**, and a **3D Tidal Distortion Field** vector overlay.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    5-STAGE ASTROPHYSICAL TIMELINE                       │
│ 01 ORDERED RING → 02 INTRUDER APPROACH → 03 CLOSE ENCOUNTER           │
│                  → 04 TIDAL RESPONSE → 05 DEBRIS EVOLUTION             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Cinematic Visual Features (NASA APOD / SVS Inspired)

### A. Soft Radial Particle Sprites & Additive Blending
- Replaces square pixel dots with procedurally generated circular radial soft glow particle textures using `THREE.AdditiveBlending`, rendering luminous plasma points with physical bloom and depth.

### B. NASA APOD Black Hole Event Horizon & Photon Ring
- Pitch-black central event horizon (`r = 1.4`) encircled by a razor-thin, brilliant photon ring outline (`RingGeometry(1.41, 1.47)`) and a procedurally lensed accretion glow halo (`opacity = 0.35`), directly matching NASA Jeremy Schnittman APOD renders.

### C. Procedural B-V Multi-Temperature Deep Space Starfield
- Renders 3,500 deep-space stars mapped according to real astronomical B-V temperature colors (hot blue O/B stars `#88c8ff`, solar yellow G stars `#fff4cc`, cool red M dwarfs `#ff9977`) with non-uniform magnitude falloff.

### D. Live Close-Approach Event Alert
- Dynamic HUD alert banner triggered automatically during intruder pericenter passage: `CLOSE APPROACH DETECTED // TIDAL STREAM IN PROGRESS`.

### E. Elevated 3D Disk Camera Framing ($35^\circ$)
- Opening camera positioned at ($22, 18, 24$), looking down onto the ring plane to showcase a wide 3D disk structure filling $80\%$ of the viewport.

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

## 5. Quick Start & Execution

### Launch WebGL Observatory (Primary Deliverable)
```bash
python main.py
```
*(Serves WebGL simulation at `http://localhost:8000` and opens browser)*

### Run Headless Energy Conservation Benchmark
```bash
python main.py --headless
```

### Run Autonomous Physics Verification Suite
```bash
python -m pytest -v tests/
```

---

## 6. Keybindings & Controls

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

## 7. Verification Suite Results

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

============================== 9 passed in 2.72s ==============================
```

---

## 8. License

Licensed under the MIT License.
