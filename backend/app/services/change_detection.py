"""Classical digital image processing change detection algorithms."""

from typing import Any, Dict, Optional, Tuple
import numpy as np
import cv2
from skimage.metrics import structural_similarity
from sklearn.decomposition import PCA
from .indices import compute_index
from .utils import normalize_to_uint8


def image_differencing(gray1: np.ndarray, gray2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Compute grayscale image differencing.

    Returns:
      (magnitude_diff, signed_diff)
    """
    g1 = gray1.astype(np.float32)
    g2 = gray2.astype(np.float32)
    signed = g2 - g1
    magnitude = np.abs(signed)
    return magnitude, signed


def index_differencing(idx1: np.ndarray, idx2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Compute spectral index differencing (after minus before).

    Returns:
      (magnitude_diff, signed_diff)
    """
    signed = idx2.astype(np.float32) - idx1.astype(np.float32)
    magnitude = np.abs(signed)
    return magnitude, signed


def pca_differencing(before_bands: np.ndarray, after_bands: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Principal Component Analysis (PCA) on stacked multi-spectral difference vectors.

    Projects multi-band differences onto the primary axis of maximum change variance.
    Returns:
      (magnitude_diff, signed_diff)
    """
    delta = (after_bands - before_bands).astype(np.float32)
    c, h, w = delta.shape

    if c == 1:
        signed = delta[0]
        return np.abs(signed), signed

    # Reshape (C, H, W) to (H*W, C)
    delta_flat = delta.reshape(c, -1).T  # (N, C)

    # Standardize data to zero mean
    delta_centered = delta_flat - np.mean(delta_flat, axis=0)

    # Apply PCA extracting 1 principal component
    pca = PCA(n_components=1, random_state=42)
    pc1_flat = pca.fit_transform(delta_centered)[:, 0]

    signed = pc1_flat.reshape(h, w)
    magnitude = np.abs(signed)
    return magnitude, signed


def change_vector_analysis(before_bands: np.ndarray, after_bands: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Change Vector Analysis (CVA) in multi-spectral feature space.

    Calculates Euclidean magnitude and dominant change direction.
    Returns:
      (magnitude, direction_signed)
    """
    delta = (after_bands - before_bands).astype(np.float32)
    # Euclidean magnitude across all spectral dimensions
    magnitude = np.sqrt(np.sum(delta ** 2, axis=0))
    # Direction: average signed direction across spectral channels
    direction_signed = np.mean(delta, axis=0)
    return magnitude, direction_signed


def ssim_change(gray1: np.ndarray, gray2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Structural Similarity Index (SSIM) based change detection.

    Computes 1 - SSIM. Low similarity corresponds to high structural change.
    Returns:
      (change_map, signed_diff)
    """
    g1 = gray1.astype(np.float32)
    g2 = gray2.astype(np.float32)

    # Scale to [0, 1] for SSIM calculation
    min_val = min(float(np.min(g1)), float(np.min(g2)))
    max_val = max(float(np.max(g1)), float(np.max(g2)))
    range_val = max_val - min_val if max_val > min_val else 1.0

    g1_norm = (g1 - min_val) / range_val
    g2_norm = (g2 - min_val) / range_val

    # SSIM full map
    _, ssim_map = structural_similarity(g1_norm, g2_norm, full=True, data_range=1.0)
    # Dissimilarity
    change_map = np.clip(1.0 - ssim_map, 0.0, 2.0).astype(np.float32)
    signed_diff = g2 - g1
    return change_map, signed_diff


def threshold_map(
    diff: np.ndarray,
    mode: str = "otsu",
    value: Optional[float] = None
) -> np.ndarray:
    """Segment continuous difference map into binary change mask (0 or 255).

    Modes:
      - 'otsu': Automatic global optimal thresholding via Otsu's method.
      - 'adaptive': Local adaptive Gaussian thresholding.
      - 'manual': Custom threshold cutoff.
    """
    diff_u8 = normalize_to_uint8(diff)

    if mode == "otsu":
        _, mask = cv2.threshold(diff_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return mask

    elif mode == "adaptive":
        mask = cv2.adaptiveThreshold(
            diff_u8,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=21,
            C=-3  # slight offset to highlight clear changes
        )
        return mask

    elif mode == "manual":
        if value is None:
            # Fallback to Otsu if no manual value passed
            _, mask = cv2.threshold(diff_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return mask

        # If value is given in normalized [0, 1] range
        if 0.0 <= value <= 1.0:
            cutoff = int(value * 255)
        else:
            cutoff = int(value)
        cutoff = max(0, min(255, cutoff))
        _, mask = cv2.threshold(diff_u8, cutoff, 255, cv2.THRESH_BINARY)
        return mask

    else:
        raise ValueError(f"Unknown threshold mode: {mode}")


def run_method(
    name: str,
    before_bands: np.ndarray,
    after_bands: np.ndarray,
    use_case: str,
    is_multispectral: bool = True,
    threshold_mode: str = "otsu",
    threshold_val: Optional[float] = None
) -> Dict[str, Any]:
    """Unified entry point for running change detection algorithms.

    Returns:
      dict with 'diff_map', 'signed_diff', 'mask', and 'method'.
    """
    name_clean = name.lower().strip()

    # Create grayscale versions for 2D methods
    if before_bands.shape[0] >= 3:
        # Green + Red + NIR or standard RGB average
        gray1 = np.mean(before_bands[:3], axis=0)
        gray2 = np.mean(after_bands[:3], axis=0)
    else:
        gray1 = before_bands[0]
        gray2 = after_bands[0]

    if name_clean in ("index_differencing", "index"):
        if not is_multispectral or before_bands.shape[0] < 3:
            raise ValueError(
                "Spectral index differencing requires multi-spectral imagery. "
                "Plain RGB images do not possess the required NIR/SWIR bands."
            )
        idx1 = compute_index(before_bands, use_case)
        idx2 = compute_index(after_bands, use_case)
        diff_mag, diff_signed = index_differencing(idx1, idx2)

    elif name_clean in ("image_differencing", "diff"):
        diff_mag, diff_signed = image_differencing(gray1, gray2)

    elif name_clean in ("pca", "pca_differencing"):
        diff_mag, diff_signed = pca_differencing(before_bands, after_bands)

    elif name_clean in ("cva", "change_vector_analysis"):
        diff_mag, diff_signed = change_vector_analysis(before_bands, after_bands)

    elif name_clean in ("ssim", "ssim_change"):
        diff_mag, diff_signed = ssim_change(gray1, gray2)

    else:
        raise ValueError(f"Unknown change detection method: {name}")

    # Generate initial segmented change mask
    mask = threshold_map(diff_mag, mode=threshold_mode, value=threshold_val)

    return {
        "method": name_clean,
        "diff_map": diff_mag.astype(np.float32),
        "signed_diff": diff_signed.astype(np.float32),
        "mask": mask.astype(np.uint8),
        "threshold_mode": threshold_mode
    }
