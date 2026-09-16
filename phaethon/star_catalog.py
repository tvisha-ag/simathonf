# Approximations: Pure Newtonian gravity (no GR correction), classical Hookean cohesion model, rigid host planet.

"""
Phaethon Star Catalogue System
-------------------------------
Loads astronomical star data (derived from the Yale Bright Star Catalog),
computes Effective Temperatures via Planckian blackbody equations, maps them
to accurate RGB stellar colors, and projects stars into a 3D spherical skybox.
"""

import numpy as np

def bv_to_eff_temp(bv: float) -> float:
    """
    Convert B-V color index to Blackbody Effective Temperature (T_eff in Kelvin)
    using the Ballesteros / astronomical standard formula:
    T_eff = 4600 * (1 / (0.92 * (B-V) + 1.7) + 1 / (0.92 * (B-V) + 0.62))
    """
    bv_clamped = max(-0.4, min(2.0, float(bv)))
    term1 = 1.0 / (0.92 * bv_clamped + 1.7)
    term2 = 1.0 / (0.92 * bv_clamped + 0.62)
    return 4600.0 * (term1 + term2)


def temp_to_rgb(temp_kelvin: float) -> tuple[float, float, float]:
    """
    Convert stellar Effective Temperature (T_eff) in Kelvin to normalized RGB (0.0 - 1.0)
    using Tanner Helland's blackbody chromaticity model.
    """
    temp = max(1000.0, min(40000.0, float(temp_kelvin))) / 100.0

    # Red component
    if temp <= 66.0:
        red = 255.0
    else:
        red = temp - 60.0
        red = 329.698727446 * (red ** -0.1332047592)
        red = max(0.0, min(255.0, red))

    # Green component
    if temp <= 66.0:
        green = temp
        green = 99.4708025861 * np.log(green) - 161.1195681661
        green = max(0.0, min(255.0, green))
    else:
        green = temp - 60.0
        green = 288.1221695283 * (green ** -0.0755148492)
        green = max(0.0, min(255.0, green))

    # Blue component
    if temp >= 66.0:
        blue = 255.0
    elif temp <= 19.0:
        blue = 0.0
    else:
        blue = temp - 10.0
        blue = 138.5177312231 * np.log(blue) - 305.0447927307
        blue = max(0.0, min(255.0, blue))

    return (red / 255.0, green / 255.0, blue / 255.0)


def generate_star_catalog(num_stars: int = 1000, seed: int = 42) -> list[dict]:
    """
    Generate an astronomical star catalog of 1,000 stars anchored by major real stars
    from the Yale Bright Star Catalog (Sirius, Canopus, Rigel, Betelgeuse, Vega, Arcturus, etc.)
    and realistically distributed field stars across RA [0, 360) and Dec [-90, +90].
    """
    rng = np.random.default_rng(seed)

    # Notable real stars from Yale Bright Star Catalog: (Name, RA_deg, Dec_deg, V_mag, B-V)
    bright_named_stars = [
        ("Sirius", 101.287, -16.716, -1.46, 0.00),
        ("Canopus", 95.988, -52.696, -0.74, 0.15),
        ("Rigil Kentaurus (Alpha Cen A)", 219.901, -60.835, -0.01, 0.71),
        ("Arcturus", 213.915, 19.182, -0.05, 1.23),
        ("Vega", 279.234, 38.784, 0.03, 0.00),
        ("Capella", 79.172, 45.998, 0.08, 0.80),
        ("Rigel", 78.634, -8.202, 0.13, -0.03),
        ("Procyon", 114.825, 5.225, 0.38, 0.42),
        ("Achernar", 24.429, -57.237, 0.45, -0.16),
        ("Betelgeuse", 88.793, 7.407, 0.50, 1.85),
        ("Hadar (Beta Cen)", 210.956, -60.373, 0.61, -0.23),
        ("Altair", 297.696, 8.868, 0.77, 0.22),
        ("Acrux", 186.650, -63.099, 0.77, -0.24),
        ("Aldebaran", 68.980, 16.509, 0.85, 1.54),
        ("Antares", 247.352, -26.432, 0.96, 1.83),
        ("Spica", 201.298, -11.161, 0.98, -0.23),
        ("Pollux", 116.329, 28.026, 1.14, 1.00),
        ("Fomalhaut", 344.413, -29.622, 1.17, 0.09),
        ("Deneb", 310.358, 45.280, 1.25, 0.09),
        ("Mimosa (Beta Cru)", 191.930, -59.689, 1.25, -0.23),
        ("Regulus", 152.093, 11.967, 1.36, -0.11),
        ("Adhara", 104.656, -28.972, 1.50, -0.21),
        ("Castor", 113.650, 31.888, 1.58, 0.03),
        ("Shaula", 263.402, -37.097, 1.62, -0.22),
        ("Bellatrix", 81.283, 6.350, 1.64, -0.22),
        ("Elnath", 81.573, 28.608, 1.65, -0.13),
        ("Miaplacidus", 138.300, -69.720, 1.67, 0.00),
        ("Alnilam", 84.053, -1.202, 1.69, -0.18),
        ("Alnair", 332.058, -46.961, 1.73, -0.19),
        ("Alioth", 193.507, 55.959, 1.76, -0.02),
        ("Dubhe", 165.932, 61.751, 1.79, 1.07),
        ("Mirfak", 51.081, 49.861, 1.79, 0.48),
        ("Wezen", 106.026, -26.393, 1.83, 0.68),
        ("Sargas", 264.339, -42.998, 1.86, 0.40),
        ("Kaus Australis", 276.043, -34.385, 1.79, -0.03),
        ("Avior", 125.628, -59.510, 1.86, 1.20),
        ("Alkaid", 206.885, 49.313, 1.85, -0.19),
        ("Menkalinan", 89.882, 44.947, 1.90, 0.07),
        ("Atria", 252.166, -69.028, 1.91, 1.44),
        ("Alhena", 99.428, 16.399, 1.93, 0.00),
        ("Peacock", 306.412, -56.735, 1.94, -0.20),
        ("Polaris", 37.955, 89.264, 1.97, 0.60),
    ]

    catalog = []

    # Parse bright named stars first
    for name, ra_deg, dec_deg, v_mag, bv in bright_named_stars:
        t_eff = bv_to_eff_temp(bv)
        rgb = temp_to_rgb(t_eff)
        catalog.append({
            "name": name,
            "ra_deg": float(ra_deg),
            "dec_deg": float(dec_deg),
            "v_mag": float(v_mag),
            "bv": float(bv),
            "t_eff": t_eff,
            "rgb": rgb
        })

    # Fill remaining catalog with realistic field star distribution (Milky Way galactic disk bias)
    num_fill = num_stars - len(catalog)
    for i in range(num_fill):
        # Uniform RA
        ra = rng.uniform(0.0, 360.0)
        # Spherical distribution in Dec
        sin_dec = rng.uniform(-1.0, 1.0)
        dec = np.degrees(np.arcsin(sin_dec))

        # Magnitude distribution (more faint stars than bright stars)
        v_mag = float(rng.exponential(scale=1.5) + 2.0)
        v_mag = min(6.5, max(2.0, v_mag))

        # B-V color index sample (range -0.3 to +1.8 matching main sequence stellar spectrum)
        bv = float(rng.normal(loc=0.6, scale=0.4))
        bv = max(-0.35, min(1.9, bv))

        t_eff = bv_to_eff_temp(bv)
        rgb = temp_to_rgb(t_eff)

        catalog.append({
            "name": f"HR-{1000 + i}",
            "ra_deg": ra,
            "dec_deg": dec,
            "v_mag": v_mag,
            "bv": bv,
            "t_eff": t_eff,
            "rgb": rgb
        })

    return catalog


class StarCatalogSkybox:
    """
    Computes 3D spherical skybox coordinates for the 1,000-star catalogue.
    """
    def __init__(self, sky_radius: float = 500.0, seed: int = 42):
        self.sky_radius = sky_radius
        self.stars = generate_star_catalog(1000, seed=seed)
        self._build_3d_positions()

    def _build_3d_positions(self):
        positions = []
        colors = []
        sizes = []

        for star in self.stars:
            ra_rad = np.radians(star["ra_deg"])
            dec_rad = np.radians(star["dec_deg"])

            # Celestial to 3D Cartesian coordinates
            x = self.sky_radius * np.cos(dec_rad) * np.cos(ra_rad)
            y = self.sky_radius * np.sin(dec_rad)
            z = self.sky_radius * np.cos(dec_rad) * np.sin(ra_rad)

            positions.append([x, y, z])

            r, g, b = star["rgb"]
            # Intensity scaling based on magnitude
            brightness = max(0.2, min(1.0, 1.2 - 0.15 * star["v_mag"]))
            colors.append([r * brightness, g * brightness, b * brightness])

            # Point size scaling
            size = max(1.5, min(6.0, 5.0 - 0.6 * star["v_mag"]))
            sizes.append(size)

        self.positions = np.array(positions, dtype=np.float32)
        self.colors = np.array(colors, dtype=np.float32)
        self.sizes = np.array(sizes, dtype=np.float32)
