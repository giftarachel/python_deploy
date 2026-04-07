"""
Core Engineering Solver: Matrix-Based Force Distribution
Uses Direction Cosine Matrix and NumPy linear algebra.

Static Equilibrium:  A · T = F
Solution:            T = A⁻¹ · F  (or least-squares for overdetermined systems)

Direction Cosine Matrix A:
  Each column i represents link i:
    A[0,i] = cos(θᵢ)   <- x-component
    A[1,i] = sin(θᵢ)   <- y-component
"""

import numpy as np


def build_direction_cosine_matrix(angles_deg: list[float]) -> np.ndarray:
    """
    Construct the Direction Cosine Matrix from link angles.
    Shape: (2, n_links) — two equilibrium equations (Fx, Fy) per link.
    """
    angles_rad = np.radians(angles_deg)
    A = np.array([
        np.cos(angles_rad),   # Fx row: F·cos(θ)
        np.sin(angles_rad),   # Fy row: F·sin(θ)
    ])
    return A


def resolve_external_force(magnitude: float, force_type: str) -> np.ndarray:
    """
    Decompose external force into [Fx, Fy] based on load type.
    - bump:      purely vertical (Fy)
    - braking:   purely horizontal (Fx)
    - cornering: 45° split between Fx and Fy
    """
    force_type = force_type.lower()
    if force_type == "bump":
        return np.array([0.0, magnitude])
    elif force_type == "braking":
        return np.array([magnitude, 0.0])
    elif force_type == "cornering":
        component = magnitude / np.sqrt(2)
        return np.array([component, component])
    else:
        return np.array([0.0, magnitude])


def solve_force_distribution(angles_deg: list[float], magnitude: float, force_type: str) -> dict:
    """
    Main solver: builds A, resolves F, solves A·T = F.

    For n == 2: exact solution via matrix inverse (A⁻¹·F).
    For n > 2:  least-squares solution (overdetermined system).
    For n == 1: direct projection.

    Returns a dict with matrix details and computed link forces T.
    """
    n = len(angles_deg)
    A = build_direction_cosine_matrix(angles_deg)
    F = resolve_external_force(magnitude, force_type)

    if n == 1:
        # Single link: project force onto link direction
        angle_rad = np.radians(angles_deg[0])
        T = np.array([F[0] * np.cos(angle_rad) + F[1] * np.sin(angle_rad)])
        method = "direct_projection"
    elif n == 2:
        # Square system: exact inverse
        try:
            T = np.linalg.solve(A, F)
            method = "matrix_inverse"
        except np.linalg.LinAlgError:
            T, _, _, _ = np.linalg.lstsq(A, F, rcond=None)
            method = "least_squares_fallback"
    else:
        # Overdetermined: least-squares minimisation
        T, _, _, _ = np.linalg.lstsq(A, F, rcond=None)
        method = "least_squares"

    # Compute residual (equilibrium check)
    residual = np.linalg.norm(A @ T - F)

    return {
        "link_forces": T.tolist(),
        "direction_cosine_matrix": A.tolist(),
        "external_force_vector": F.tolist(),
        "method": method,
        "residual": round(float(residual), 6),
        "max_stress_link": int(np.argmax(np.abs(T))),
    }
