# Phaethon: Relativistic Tidal Ring Disruption & Spacetime Engine
**Simathon Competition Edition — NASA/JPL Observatory Overhaul**

[![Physics Tests](https://img.shields.io/badge/Physics_Suite-9%2F9_Passed-00f0ff.svg)](#verification-suite)
[![License](https://img.shields.io/badge/License-MIT-gold.svg)](#license)

---

## 1. Project Overview

**Phaethon** is an interactive, physically defensible WebGL and Python astrophysics simulation built for scientific visualization and creative coding competitions.

Designed as a **NASA/JPL Mission-Control Computational Observatory**, the simulation models the **tidal disruption of a pristine icy particle ring** orbiting a supermassive Central Black Hole ($M_{\text{BH}} = 100\,M_\odot$) when perturbed by an eccentric, inclined Stellar Intruder ($M_{\text{star}} = 15\,M_\odot$).

Unlike generic particle systems or simplified sphere animations, Phaethon calculates differential gravitational forces across $5,000\text{--}20,000$ collisionless test particles using a 2nd-order **Symplectic Velocity Verlet** numerical integrator with optional **1PN Schwarzschild Post-Newtonian relativistic precession** and a live **3D Tidal Distortion Field** vector overlay.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    5-STAGE ASTROPHYSICAL TIMELINE                       │
│ 01 ORDERED RING → 02 INTRUDER APPROACH → 03 CLOSE ENCOUNTER           │
│                  → 04 TIDAL RESPONSE → 05 DEBRIS EVOLUTION             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Key Scientific Features

### A. NASA/JPL Mission-Control Aesthetic
- **Top Bar**: Displays `PHAETHON // TIDAL RING OBSERVATORY`, real-time 5-stage encounter timeline, and live simulation status badges (`ACTIVE` / `PAUSED`).
- **Sidebar Telemetry**: Clean dark slate HUD (`rgba(4, 9, 18, 0.9)`) displaying physical constants ($M_{\text{BH}}$, $M_{\text{star}}$), orbital separation ($\text{AU}$), maximum tidal acceleration, perturbed particle gauge, and live Hamiltonian energy drift plot canvas.

### B. 3D Tidal Distortion Field Vector Overlay (`T` Key / Toggle)
- Toggling `TIDAL FIELD: ON` renders a dynamic sparse 3D vector field display showing differential gravitational acceleration arrows $\Delta \mathbf{a}_{\text{tidal}} = \mathbf{a}_{\text{star}} - \mathbf{a}_{\text{BH-COM}}$, visually demonstrating *why* differential forces pull the ring apart.

### C. 5-Stage Encounter Progress Bar
1. **`01 — ORDERED RING`**: Pristine circular Keplerian orbit ($v_c = \sqrt{G M / r}$).
2. **`02 — INTRUDER APPROACH`**: Stellar intruder approaching ring plane along eccentric trajectory.
3. **`03 — CLOSE ENCOUNTER`**: Pericenter passage ($r \le 10\,\text{AU}$).
4. **`04 — TIDAL RESPONSE`**: Asymmetric gravitational stretching of ring particles into density waves.
5. **`05 — DEBRIS EVOLUTION`**: Long-term tidal stream formation and high-energy debris escape.

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

where $M_{\text{BH}} = 100\,M_\odot$, $M_{\text{star}} = 15\,M_\odot$, and $\epsilon = 0.15\;\text{AU}$ (Plummer softening).

### Weak-Field 1PN Relativistic Precession (`RELATIVITY: ON/OFF`)
$$\mathbf{a}_{\text{1PN}} = -\frac{3 G M_{\text{BH}} L_i^2}{c_{\text{eff}}^2 r_i^5} \mathbf{r}_i \quad \text{where } \mathbf{L}_i = \mathbf{r}_i \times \mathbf{v}_i$$

---

## 4. Continuous Physical Color Mapping

Particle colors carry direct physical meaning based on orbital energy perturbation relative to their initial circular Keplerian state ($\text{Dev}_i = |E_i(t) - E_{i,0}| / |E_{i,0}|$):

| Perturbation $\text{Dev}_i$ | Color | Physical Meaning |
|---|---|---|
| $< 0.05$ | **Cool Cyan** (`#00f0ff`) | Stable / Unperturbed Keplerian Orbit |
| $0.05 \le \text{Dev}_i < 0.20$ | **Stellar Gold** (`#ffd700`) | Moderately Perturbed / Density Wave |
| $0.20 \le \text{Dev}_i < 0.50$ | **Hot Crimson** (`#ff4500`) | Strongly Perturbed / Tidal Stream |
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

============================== 9 passed in 1.73s ==============================
```

---

## 8. License

Licensed under the MIT License.
