# Phaethon: Relativistic Tidal Ring Disruption & Spacetime Engine
**Simathon Competition Edition — Astrophysics Visualization Suite**

[![Physics Tests](https://img.shields.io/badge/Physics_Suite-9%2F9_Passed-00f0ff.svg)](#verification-suite)
[![License](https://img.shields.io/badge/License-MIT-gold.svg)](#license)

---

## 1. Project Overview

**Phaethon** is an interactive, physically defensible WebGL and Python astrophysics simulation built for scientific visualization and creative coding competitions.

The simulation models the **tidal disruption of a pristine icy particle ring** orbiting a supermassive Central Black Hole ($M_{\text{BH}} = 100\,M_\odot$) when perturbed by an eccentric, inclined Stellar Intruder ($M_{\text{star}} = 15\,M_\odot$).

Unlike generic particle systems or simplified sphere animations, Phaethon calculates differential gravitational forces across $5,000\text{--}20,000$ collisionless test particles using a 2nd-order **Symplectic Velocity Verlet** numerical integrator with optional **1PN Schwarzschild Post-Newtonian relativistic precession**.

```
    PRISTINE RING
          ↓
    INTRUDER APPROACH
          ↓
    CLOSE ENCOUNTER
          ↓
    DIFFERENTIAL GRAVITY
          ↓
    TIDAL DEFORMATION
          ↓
    DEBRIS STREAMS AND DENSITY WAVES
          ↓
    LONG-TERM ORBITAL EVOLUTION
```

---

## 2. Scientific Question

> *How does a massive stellar intruder alter the orbital distribution and energy state of particles in a dense, coherent ring through differential gravitational perturbation?*

As the intruder approaches pericenter, particles closest to the intruder experience a stronger gravitational acceleration than the central black hole alone provides. This differential acceleration ($\Delta \mathbf{a}_{\text{tidal}}$) causes:
1. Orbital energy shifts ($\Delta E / E_0$).
2. Formation of density waves, ring gaps, and eccentric stream structures.
3. Ejection of high-energy debris along tidal arms.

---

## 3. Physical Model & Equations

### Unit System & Constants
The simulation operates in standard astronomical units:
- **Length**: Astronomical Units ($\text{AU}$)
- **Mass**: Solar Masses ($M_\odot$)
- **Time**: Years ($\text{yr}$)

In this unit system, the gravitational constant is:
$$G = 4\pi^2 \approx 39.47841760435743\;\text{AU}^3\,M_\odot^{-1}\,\text{yr}^{-2}$$

### Gravitational Acceleration
For each ring test particle $i$ with position $\mathbf{r}_i$ and velocity $\mathbf{v}_i$:

$$\mathbf{a}_i = -\frac{G M_{\text{BH}} \mathbf{r}_i}{|\mathbf{r}_i|^3} - \frac{G M_{\text{star}} (\mathbf{r}_i - \mathbf{r}_{\text{star}})}{\left(|\mathbf{r}_i - \mathbf{r}_{\text{star}}|^2 + \epsilon^2\right)^{3/2}} + \mathbf{a}_{\text{1PN}}$$

where:
- $M_{\text{BH}} = 100\,M_\odot$ is the central black hole mass.
- $M_{\text{star}} = 15\,M_\odot$ is the stellar intruder mass.
- $\epsilon = 0.15\;\text{AU}$ is the Plummer softening parameter preventing unphysical close-encounter divergence.

### Weak-Field 1PN Relativistic Precession (`RELATIVITY: ON/OFF`)
When relativity mode is enabled, a leading-order post-Newtonian (1PN) Schwarzschild perihelion precession acceleration is added:

$$\mathbf{a}_{\text{1PN}} = -\frac{3 G M_{\text{BH}} L_i^2}{c_{\text{eff}}^2 r_i^5} \mathbf{r}_i$$

where $\mathbf{L}_i = \mathbf{r}_i \times \mathbf{v}_i$ is the specific angular momentum vector.

---

## 4. Numerical Integration

Phaethon employs a 2nd-order **Symplectic Velocity Verlet** numerical integrator:

1. **First Half-Kick**:
   $$\mathbf{v}_{i}(t + \tfrac{1}{2}\Delta t) = \mathbf{v}_i(t) + \tfrac{1}{2} \mathbf{a}_i(t) \Delta t$$
2. **Position Drift**:
   $$\mathbf{r}_i(t + \Delta t) = \mathbf{r}_i(t) + \mathbf{v}_i(t + \tfrac{1}{2}\Delta t) \Delta t$$
3. **Recompute Acceleration**:
   $$\mathbf{a}_i(t + \Delta t) = \mathbf{a}\left(\mathbf{r}_i(t + \Delta t), \mathbf{v}_i(t + \tfrac{1}{2}\Delta t), \mathbf{r}_{\text{star}}(t + \Delta t)\right)$$
4. **Second Half-Kick**:
   $$\mathbf{v}_i(t + \Delta t) = \mathbf{v}_i(t + \tfrac{1}{2}\Delta t) + \tfrac{1}{2} \mathbf{a}_i(t + \Delta t) \Delta t$$

The symplectic nature of the integrator preserves phase space volume and maintains Hamiltonian energy conservation ($|\Delta E / E_0| < 10^{-4}$) over thousands of orbits for unperturbed particles.

---

## 5. Particle Model & $O(N)$ Optimization

Ring particles are modeled as **collisionless test particles** moving in the joint gravitational field of the central black hole and stellar intruder. 
- Self-gravity between individual ring particles ($O(N^2)$) is omitted, as ring particle masses are negligible compared to $M_{\text{BH}}$ and $M_{\text{star}}$.
- This keeps the force calculation at $O(N)$ complexity, allowing real-time rendering of $5,000\text{--}20,000$ particles at 60+ FPS in WebGL.

---

## 6. Continuous Physical Color Mapping

Particle colors carry direct physical meaning based on orbital energy perturbation relative to their initial circular Keplerian state:

$$\text{Dev}_i = \frac{|E_i(t) - E_{i,0}|}{|E_{i,0}|}$$

| Perturbation $\text{Dev}_i$ | Color | Physical Meaning |
|---|---|---|
| $< 0.05$ | **Cool Cyan** (`#00f0ff`) | Stable / Unperturbed Keplerian Orbit |
| $0.05 \le \text{Dev}_i < 0.20$ | **Stellar Gold** (`#ffd700`) | Moderately Perturbed / Density Wave |
| $0.20 \le \text{Dev}_i < 0.50$ | **Hot Crimson** (`#ff4500`) | Strongly Perturbed / Tidal Stream |
| $\ge 0.50$ | **White-Hot Plasma** (`#ffffff`) | High-Energy Escaping Debris |

---

## 7. Installation & Quick Start

### Prerequisites
- Python 3.9+
- Web browser with WebGL 2 support (Chrome, Firefox, Edge, Safari)

### Quick Run (WebGL Interface)
```bash
python main.py
```
This launches a local web server at `http://localhost:8000` and automatically opens the interactive WebGL simulation in your browser.

### Run Headless Energy Conservation Benchmark
```bash
python main.py --headless
```

### Run Autonomous Physics Verification Suite
```bash
python -m pytest -v tests/
```

---

## 8. Controls & User Interface

| Input | Action |
|---|---|
| **`SPACE`** | Pause / Resume simulation |
| **`R`** | Reset ring & intruder to initial state |
| **`W`** / **`UP`** | Increase simulation speed ($+0.5\times$) |
| **`S`** / **`DOWN`** | Decrease simulation speed ($-0.5\times$) |
| **`ESC`** | Reset camera view |
| **Mouse Drag** | Arcball orbit camera rotation |
| **Mouse Scroll** | Camera zoom in / out |
| **UI Toggle `RELATIVITY`** | Switch between Newtonian and 1PN Precession modes |
| **Particle Count Dropdown** | Select $5,000$, $10,000$, or $20,000$ particles |

---

## 9. Verification Suite Results

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

============================== 9 passed in 1.88s ==============================
```

---

## 10. Best Screenshot Moments

For competition presentation or screenshot capture, recommended camera angles and moments:
1. **Initial State ($t = 0.0\,\text{yr}$)**: Camera elevated at $30^\circ$, showing the pristine cyan multi-band ring surrounding the dark central Black Hole with its photon ring glow.
2. **First Close Encounter ($t \approx 3.5\,\text{yr}$)**: The stellar intruder reaches pericenter ($4.2\,\text{AU}$), pulling an asymmetric wave of gold and crimson particles out of the ring.
3. **Tidal Stream & Gap ($t \approx 6.0\,\text{yr}$)**: High-energy white debris streams shoot across the viewport, leaving a prominent gap in the outer ring.

---

## 11. License

Licensed under the MIT License.
