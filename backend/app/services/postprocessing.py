"""Postprocessing: morphology, region filtering, overlays, statistics, and GeoJSON export."""

from typing import Any, Dict, Optional, Tuple
import numpy as np
import cv2
import rasterio.features
from rasterio.warp import transform_geom
from .utils import normalize_to_uint8


def morphological_cleanup(mask: np.ndarray, ksize: int = 5) -> np.ndarray:
    """Apply morphological Opening (removes salt noise) followed by Closing (fills gaps).

    Uses an elliptical structuring element.
    """
    if ksize % 2 == 0:
        ksize += 1
    ksize = max(3, ksize)

    bin_mask = (mask > 0).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))

    # Opening: Erosion then Dilation
    opened = cv2.morphologyEx(bin_mask, cv2.MORPH_OPEN, kernel)
    # Closing: Dilation then Erosion
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

    return closed


def remove_small_regions(mask: np.ndarray, min_area: int = 50) -> np.ndarray:
    """Filter out small disconnected noise patches below min_area pixels."""
    bin_mask = (mask > 0).astype(np.uint8) * 255
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(bin_mask, connectivity=8)

    clean_mask = np.zeros_like(bin_mask)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_area:
            clean_mask[labels == i] = 255

    return clean_mask


def make_overlay(
    after_rgb: np.ndarray,
    mask: np.ndarray,
    color: Tuple[int, int, int] = (239, 68, 68),
    alpha: float = 0.45
) -> np.ndarray:
    """Create a semi-transparent colored change overlay onto the after image.

    color: (R, G, B) tuple.
    Returns:
      uint8 RGB image of shape (H, W, 3).
    """
    # Prepare base image in uint8 RGB of shape (H, W, 3)
    if after_rgb.ndim == 2:
        base = np.stack([after_rgb] * 3, axis=-1)
    elif after_rgb.ndim == 3:
        if after_rgb.shape[-1] == 3:
            base = after_rgb.copy()
        elif after_rgb.shape[0] == 1:
            base = np.stack([after_rgb[0]] * 3, axis=-1)
        elif after_rgb.shape[0] >= 3:
            # Multi-channel (C, H, W).
            # For 5-band Sentinel-2 [Green=0, Red=1, NIR=2, SWIR1=3, SWIR2=4]:
            if after_rgb.shape[0] >= 5:
                # RGB preview: Red=band 1, Green=band 0, Blue synthesized
                b_chan = np.clip(after_rgb[0] * 0.85, 0.0, 1.0)
                base = np.stack([after_rgb[1], after_rgb[0], b_chan], axis=-1)
            else:
                base = np.transpose(after_rgb[:3], (1, 2, 0))
        else:
            base = np.stack([after_rgb[0]] * 3, axis=-1)
    else:
        raise ValueError(f"Unsupported image shape for overlay: {after_rgb.shape}")

    if base.dtype != np.uint8:
        base = normalize_to_uint8(base)

    overlay = base.copy().astype(np.float32)
    change_pixels = (mask > 0)

    col = np.array(color, dtype=np.float32)
    overlay[change_pixels] = (1.0 - alpha) * overlay[change_pixels] + alpha * col

    return np.clip(overlay, 0, 255).astype(np.uint8)


def classify_gain_loss(
    signed_diff: np.ndarray,
    mask: np.ndarray,
    use_case: str = "deforestation"
) -> Tuple[np.ndarray, np.ndarray]:
    """Segment the binary change mask into Gain and Loss masks.

    Returns:
      (gain_mask, loss_mask) each as uint8 (0 or 255).
    """
    uc = use_case.lower().strip()
    active = mask > 0

    if uc == "urbanization":
        # Built-up expansion: positive NDBI increase is Gain
        gain = active & (signed_diff > 0)
        loss = active & (signed_diff < 0)
    else:
        # Deforestation, Water shrinking, Burn scars:
        # Negative index drop is Loss (vegetation loss, water receding, burn severity)
        loss = active & (signed_diff < 0)
        gain = active & (signed_diff > 0)

    gain_u8 = (gain.astype(np.uint8)) * 255
    loss_u8 = (loss.astype(np.uint8)) * 255
    return gain_u8, loss_u8


def compute_statistics(
    mask: np.ndarray,
    signed_diff: np.ndarray,
    pixel_area_m2: float = 100.0,
    use_case: str = "deforestation"
) -> Dict[str, Any]:
    """Compute quantitative environmental metrics and change summary."""
    total_pixels = int(mask.size)
    changed_pixels = int(np.count_nonzero(mask > 0))

    changed_km2 = round(float(changed_pixels * pixel_area_m2 / 1_000_000.0), 4)
    percent_change = round(float(changed_pixels / total_pixels * 100.0), 2) if total_pixels > 0 else 0.0

    gain_mask, loss_mask = classify_gain_loss(signed_diff, mask, use_case)
    gain_pixels = int(np.count_nonzero(gain_mask > 0))
    loss_pixels = int(np.count_nonzero(loss_mask > 0))

    gain_km2 = round(float(gain_pixels * pixel_area_m2 / 1_000_000.0), 4)
    loss_km2 = round(float(loss_pixels * pixel_area_m2 / 1_000_000.0), 4)

    # Number of discrete contiguous change patches
    num_labels, _, _, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), connectivity=8)
    num_regions = max(0, int(num_labels - 1))

    return {
        "total_pixels": total_pixels,
        "changed_pixels": changed_pixels,
        "changed_km2": changed_km2,
        "percent_change": percent_change,
        "gain_km2": gain_km2,
        "loss_km2": loss_km2,
        "gain_pixels": gain_pixels,
        "loss_pixels": loss_pixels,
        "num_regions": num_regions,
        "pixel_area_m2": float(pixel_area_m2)
    }


def mask_to_geojson(
    mask: np.ndarray,
    transform: Optional[Any] = None,
    crs: Optional[Any] = None,
    max_features: int = 500
) -> Dict[str, Any]:
    """Convert binary change mask to GeoJSON polygons.

    Reprojects to EPSG:4326 when georeferenced, or pixel coordinates otherwise.
    """
    bin_mask = (mask > 0).astype(np.uint8)

    features = []
    # If transform is provided, extract shapes with affine transform
    shapes_gen = rasterio.features.shapes(bin_mask, mask=(bin_mask == 1), transform=transform)

    dst_crs = "EPSG:4326"
    need_reproject = bool(crs is not None and str(crs).upper() != dst_crs)

    for i, (geom, val) in enumerate(shapes_gen):
        if i >= max_features:
            break

        # Reproject to WGS84 EPSG:4326 if needed
        if need_reproject:
            try:
                geom = transform_geom(crs, dst_crs, geom)
            except Exception:
                pass

        features.append({
            "type": "Feature",
            "id": i,
            "properties": {
                "region_id": i + 1,
                "change_type": "detected_change"
            },
            "geometry": geom
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }
