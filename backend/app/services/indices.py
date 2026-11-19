"""Spectral indices computation for environmental monitoring."""

from typing import Any, Dict
import numpy as np

# Sentinel-2 Band index constants for 5-band stack:
# B03 (Green), B04 (Red), B08 (NIR), B11 (SWIR1), B12 (SWIR2)
BAND_GREEN = 0
BAND_RED = 1
BAND_NIR = 2
BAND_SWIR1 = 3
BAND_SWIR2 = 4

USE_CASES: Dict[str, Dict[str, Any]] = {
    "deforestation": {
        "id": "deforestation",
        "name": "Deforestation",
        "index_name": "NDVI",
        "full_index_name": "Normalized Difference Vegetation Index",
        "formula": "(NIR - Red) / (NIR + Red)",
        "accent_color": "#22c55e",
        "target_direction": "loss",  # Vegetation loss is primary concern
        "description": "Monitors loss of tree canopy and forest cover via NDVI degradation."
    },
    "water": {
        "id": "water",
        "name": "Water Body Shrinking",
        "index_name": "NDWI",
        "full_index_name": "Normalized Difference Water Index",
        "formula": "(Green - NIR) / (Green + NIR)",
        "accent_color": "#06b6d4",
        "target_direction": "both",  # Monitors both surface drying and flood expansion
        "description": "Tracks lake, reservoir, and wetland fluctuations using McFeeters NDWI."
    },
    "burn_scars": {
        "id": "burn_scars",
        "name": "Burn Scars",
        "index_name": "NBR",
        "full_index_name": "Normalized Burn Ratio",
        "formula": "(NIR - SWIR2) / (NIR + SWIR2)",
        "accent_color": "#ef4444",
        "target_direction": "loss",  # Post-fire vegetation loss causes sharp NBR drop
        "description": "Delineates wildfire burn perimeters and severity using NIR and SWIR2."
    },
    "urbanization": {
        "id": "urbanization",
        "name": "Urbanization",
        "index_name": "NDBI",
        "full_index_name": "Normalized Difference Built-up Index",
        "formula": "(SWIR1 - NIR) / (SWIR1 + NIR)",
        "accent_color": "#a855f7",
        "target_direction": "gain",  # Built-up expansion results in positive NDBI jump
        "description": "Quantifies urban sprawl, construction, and impervious surface growth."
    }
}


def _calc_normalized_diff(band_a: np.ndarray, band_b: np.ndarray, eps: float = 1e-7) -> np.ndarray:
    """Safe normalized difference (band_a - band_b) / (band_a + band_b + eps)."""
    a = band_a.astype(np.float32)
    b = band_b.astype(np.float32)
    denom = a + b
    # Avoid zero division
    denom = np.where(np.abs(denom) < eps, eps, denom)
    index = (a - b) / denom
    return np.clip(index, -1.0, 1.0).astype(np.float32)


def ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """Normalized Difference Vegetation Index: (NIR - Red) / (NIR + Red)."""
    return _calc_normalized_diff(nir, red)


def ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Normalized Difference Water Index: (Green - NIR) / (Green + NIR)."""
    return _calc_normalized_diff(green, nir)


def nbr(nir: np.ndarray, swir2: np.ndarray) -> np.ndarray:
    """Normalized Burn Ratio: (NIR - SWIR2) / (NIR + SWIR2)."""
    return _calc_normalized_diff(nir, swir2)


def ndbi(swir1: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Normalized Difference Built-up Index: (SWIR1 - NIR) / (SWIR1 + NIR)."""
    return _calc_normalized_diff(swir1, nir)


def compute_index(bands: np.ndarray, use_case: str) -> np.ndarray:
    """Compute the appropriate spectral index for the given use case.

    Requires at least 5 bands in Sentinel-2 order:
    [Green, Red, NIR, SWIR1, SWIR2].
    """
    if bands.shape[0] < 3:
        raise ValueError("At least 3 bands are required to compute spectral indices.")

    uc = use_case.lower().strip()
    if uc == "deforestation":
        return ndvi(nir=bands[BAND_NIR], red=bands[BAND_RED])
    elif uc in ("water", "water_shrinking"):
        return ndwi(green=bands[BAND_GREEN], nir=bands[BAND_NIR])
    elif uc in ("burn_scars", "burn"):
        if bands.shape[0] < 5:
            raise ValueError("NBR requires SWIR2 (band 5) from Sentinel-2.")
        return nbr(nir=bands[BAND_NIR], swir2=bands[BAND_SWIR2])
    elif uc in ("urbanization", "urban"):
        if bands.shape[0] < 4:
            raise ValueError("NDBI requires SWIR1 (band 4) from Sentinel-2.")
        return ndbi(swir1=bands[BAND_SWIR1], nir=bands[BAND_NIR])
    else:
        raise ValueError(f"Unknown use case for index computation: {use_case}")
