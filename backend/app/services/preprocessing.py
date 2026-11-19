"""Preprocessing module for noise reduction, histogram matching, and cloud masking."""

from typing import Tuple
import numpy as np
import cv2
from scipy.ndimage import median_filter
from skimage.exposure import match_histograms


def denoise(img: np.ndarray, method: str = "gaussian", ksize: int = 3) -> np.ndarray:
    """Apply spatial denoising (Gaussian blur or median filter).

    Accepts 2D (H, W) or 3D (C, H, W) float32 arrays.
    """
    if ksize % 2 == 0:
        ksize += 1
    ksize = max(3, ksize)

    if img.ndim == 2:
        if method == "median":
            return median_filter(img, size=ksize).astype(np.float32)
        # Default Gaussian
        return cv2.GaussianBlur(img.astype(np.float32), (ksize, ksize), 0).astype(np.float32)

    if img.ndim == 3:
        # (C, H, W)
        c, h, w = img.shape
        out = np.zeros_like(img, dtype=np.float32)
        for i in range(c):
            if method == "median":
                out[i] = median_filter(img[i], size=ksize)
            else:
                out[i] = cv2.GaussianBlur(img[i].astype(np.float32), (ksize, ksize), 0)
        return out

    raise ValueError(f"Unsupported array shape for denoising: {img.shape}")


def histogram_match(source: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Match histogram of source image to reference image to calibrate radiometric differences.

    Supports (C, H, W) or (H, W) float32 arrays.
    """
    if source.ndim == 2:
        matched = match_histograms(source, reference)
        return matched.astype(np.float32)

    if source.ndim == 3:
        c = source.shape[0]
        matched = np.zeros_like(source, dtype=np.float32)
        for i in range(c):
            # Match each spectral band individually
            matched[i] = match_histograms(source[i], reference[i])
        return matched

    raise ValueError(f"Unsupported shape for histogram matching: {source.shape}")


def cloud_mask(bands: np.ndarray, brightness_thresh: float = 0.88) -> np.ndarray:
    """Detect cloud and bright saturated anomalies (top reflectance).

    Returns boolean mask (H, W) where True indicates cloudy/invalid pixels.
    """
    max_v = float(np.nanmax(bands)) if bands.size > 0 else 1.0
    thresh = brightness_thresh if max_v <= 1.0 else (brightness_thresh * (65535.0 if max_v > 255.0 else 255.0))

    if bands.ndim == 2:
        return bands > thresh

    c, h, w = bands.shape
    if c >= 3:
        vis_nir_mean = np.mean(bands[:3], axis=0)
        return (vis_nir_mean > thresh).astype(bool)

    return (np.mean(bands, axis=0) > thresh).astype(bool)


def preprocess_pair(
    before: np.ndarray,
    after: np.ndarray,
    do_denoise: bool = True,
    do_match: bool = True,
    denoise_method: str = "gaussian",
    ksize: int = 3
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Clean, denoise, and radiometrically normalize an image pair.

    Returns:
      (cleaned_before, cleaned_after, valid_mask)
    """
    # Clean any NaNs or Infs
    b_clean = np.nan_to_num(before.astype(np.float32), nan=0.0, posinf=1.0, neginf=0.0)
    a_clean = np.nan_to_num(after.astype(np.float32), nan=0.0, posinf=1.0, neginf=0.0)

    # Optional spatial denoising
    if do_denoise:
        b_clean = denoise(b_clean, method=denoise_method, ksize=ksize)
        a_clean = denoise(a_clean, method=denoise_method, ksize=ksize)

    # Optional radiometric normalization via histogram matching
    if do_match:
        a_clean = histogram_match(a_clean, b_clean)

    # Compute valid pixel mask (exclude clouds and non-data zeros)
    cloud_b = cloud_mask(b_clean)
    cloud_a = cloud_mask(a_clean)
    valid_mask = (~cloud_b) & (~cloud_a)

    return b_clean, a_clean, valid_mask

