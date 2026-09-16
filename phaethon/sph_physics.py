# Approximations: Central Newtonian gravity with weak-field 1PN Schwarzschild perihelion precession correction term and N-body gravitational perturbation from a massive stellar intruder. Collisionless test-particle ring model.

"""
Phaethon Hydrodynamic & Collisionless Ring Physics Engine
---------------------------------------------------------
Provides compatibility layer and re-exports collisionless tidal ring integration.
"""

import numpy as np
from phaethon.physics import G_CONST, C_LIGHT, CentralBlackHole, StellarIntruder, CollisionlessTidalRing, SymplecticRingIntegrator

# Export for test suite compatibility
__all__ = [
    "G_CONST",
    "C_LIGHT",
    "CentralBlackHole",
    "StellarIntruder",
    "CollisionlessTidalRing",
    "SymplecticRingIntegrator"
]
