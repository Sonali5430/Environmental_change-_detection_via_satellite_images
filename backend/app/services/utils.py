"""Utility functions for image I/O, normalization, georeferencing, and synthetic data generation."""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import math
import numpy as np
import cv2
import rasterio
from rasterio.transform import from_origin
from rasterio.crs import CRS


def load_image(path: str) -> Dict[str, Any]:
    """Load an image (GeoTIFF or standard RGB/grayscale).

    Returns a dictionary containing:
      - bands: np.ndarray of shape (C, H, W) float32
      - transform: rasterio Affine transform or None
      - crs: rasterio CRS or None
      - is_georeferenced: bool
      - is_multispectral: bool (True if bands >= 4)
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found at: {path}")

    # Attempt to read with rasterio (handles GeoTIFFs and standard formats)
    try:
        with rasterio.open(path) as src:
            bands = src.read().astype(np.float32)
            transform = src.transform
            crs = src.crs

            # Check if nodata is defined and mask it
            if src.nodata is not None:
                bands[bands == src.nodata] = np.nan

            is_georef = bool(crs is not None and transform is not None and not transform.is_identity)
            c, h, w = bands.shape

            # If plain single or 3-band image without projection
            is_multi = bool(c >= 4)

            # If pixel values are uint8 (0-255) or uint16 (0-65535), keep float32
            # Handle NaNs
            if np.isnan(bands).any():
                bands = np.nan_to_num(bands, nan=0.0)

            # Standardize pixel values to [0.0, 1.0] reflectance range
            max_v = float(np.nanmax(bands))
            if max_v > 1000.0:
                divisor = 65535.0 if max_v > 10000.0 else 10000.0
                bands = bands / divisor
            elif max_v > 1.0:
                bands = bands / 255.0
            bands = np.clip(bands, 0.0, 1.0)

            return {
                "bands": bands,
                "transform": transform,
                "crs": crs,
                "is_georeferenced": is_georef,
                "is_multispectral": is_multi,
                "shape": (c, h, w)
            }
    except Exception:
        # Fallback to OpenCV for standard RGB / grayscale images
        img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"Failed to decode image from: {path}")

        if img.ndim == 2:
            # Grayscale -> (1, H, W)
            bands = img[np.newaxis, :, :].astype(np.float32)
        elif img.ndim == 3:
            # OpenCV BGR -> RGB and transpose to (C, H, W)
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            bands = np.transpose(rgb, (2, 0, 1)).astype(np.float32)
        else:
            raise ValueError(f"Unsupported image dimensions: {img.shape}")

        c, h, w = bands.shape
        return {
            "bands": bands,
            "transform": None,
            "crs": None,
            "is_georeferenced": False,
            "is_multispectral": False,
            "shape": (c, h, w)
        }


def normalize_to_uint8(array: np.ndarray, low_pct: float = 2.0, high_pct: float = 98.0) -> np.ndarray:
    """Normalize any 2D or 3D numeric array to uint8 (0-255) for display."""
    arr = np.nan_to_num(array.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)

    # If it's a binary mask already (0 and 1)
    unique_vals = np.unique(arr)
    if len(unique_vals) <= 2 and set(unique_vals).issubset({0.0, 1.0}):
        return (arr * 255).astype(np.uint8)

    # Percentile clipping to enhance contrast while ignoring outliers
    vmin = float(np.percentile(arr, low_pct))
    vmax = float(np.percentile(arr, high_pct))

    if vmax <= vmin:
        vmin = float(np.min(arr))
        vmax = float(np.max(arr))

    if vmax > vmin:
        norm = np.clip((arr - vmin) / (vmax - vmin), 0.0, 1.0) * 255.0
        return norm.astype(np.uint8)
    return np.zeros_like(arr, dtype=np.uint8)


def get_rgb_preview(bands: np.ndarray) -> np.ndarray:
    """Convert any 2D or (C, H, W) bands array into a clean uint8 (H, W, 3) RGB image."""
    arr = bands.copy()
    if arr.ndim == 2:
        u8 = normalize_to_uint8(arr)
        return np.stack([u8] * 3, axis=-1)

    c, h, w = arr.shape
    if c >= 5:
        # Sentinel-2 5 bands: Green=0, Red=1, NIR=2, SWIR1=3, SWIR2=4
        r = normalize_to_uint8(arr[1])
        g = normalize_to_uint8(arr[0])
        b = normalize_to_uint8(arr[0] * 0.85)
        return np.stack([r, g, b], axis=-1)
    elif c >= 3:
        r = normalize_to_uint8(arr[0])
        g = normalize_to_uint8(arr[1])
        b = normalize_to_uint8(arr[2])
        return np.stack([r, g, b], axis=-1)
    else:
        u8 = normalize_to_uint8(arr[0])
        return np.stack([u8] * 3, axis=-1)


def save_png(array: np.ndarray, path: str) -> str:
    """Save a 2D or 3D numpy array as a PNG image."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    arr = array.copy()

    # If shape is (C, H, W)
    if arr.ndim == 3:
        if arr.shape[0] in (1, 3, 4, 5):
            arr = get_rgb_preview(arr)
        elif arr.shape[-1] not in (1, 3, 4):
            arr = get_rgb_preview(arr)

    if arr.dtype != np.uint8:
        arr = normalize_to_uint8(arr)

    # OpenCV expects BGR for 3-channel images
    if arr.ndim == 3 and arr.shape[2] == 3:
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(p), bgr)
    else:
        cv2.imwrite(str(p), arr)

    return str(p)


def pixel_area_m2(transform: Optional[Any] = None, crs: Optional[Any] = None) -> float:
    """Calculate the ground pixel area in square meters from affine transform and CRS.

    Fallback: 100 m² (equivalent to 10 m resolution Sentinel-2 pixels).
    """
    if transform is None:
        return 100.0

    try:
        res_x = abs(float(transform.a))
        res_y = abs(float(transform.e))

        if res_x == 0 or res_y == 0:
            return 100.0

        if crs is not None and getattr(crs, "is_geographic", False):
            # Coordinates are in degrees (WGS84). 1 deg approx 111,320m at equator
            # Approximate using center latitude
            lat_deg = float(transform.f - (res_y * 256))
            lat_rad = math.radians(lat_deg)
            m_per_deg_lon = 111320.0 * math.cos(lat_rad)
            m_per_deg_lat = 110540.0
            return float(abs(res_x * m_per_deg_lon * res_y * m_per_deg_lat))

        # Projected CRS (UTM etc. where units are in meters)
        return float(res_x * res_y)
    except Exception:
        return 100.0


def generate_synthetic_pair(
    use_case: str = "deforestation",
    size: int = 512,
    base_dir: Optional[str] = None
) -> Dict[str, str]:
    """Generate a synthetic before/after Sentinel-2 5-band pair and ground truth.

    Band order:
      0: B03 (Green)
      1: B04 (Red)
      2: B08 (NIR)
      3: B11 (SWIR1)
      4: B12 (SWIR2)

    Saves:
      - data/raw/<use_case>/before.tif
      - data/raw/<use_case>/after.tif
      - data/ground_truth/<use_case>/ground_truth.png
    """
    if base_dir is None:
        # Default project root: parent of backend
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parents[2]
    else:
        project_root = Path(base_dir)

    raw_dir = project_root / "data" / "raw" / use_case
    gt_dir = project_root / "data" / "ground_truth" / use_case
    raw_dir.mkdir(parents=True, exist_ok=True)
    gt_dir.mkdir(parents=True, exist_ok=True)

    np.random.seed(42)

    # Create spatial coordinate grids
    y, x = np.ogrid[:size, :size]
    cy, cx = size // 2, size // 2

    # Smooth base terrain texture
    noise = np.random.normal(0, 0.02, (5, size, size)).astype(np.float32)
    blur_noise = np.zeros_like(noise)
    for b in range(5):
        blur_noise[b] = cv2.GaussianBlur(noise[b], (15, 15), 0)

    before = np.zeros((5, size, size), dtype=np.float32)
    after = np.zeros((5, size, size), dtype=np.float32)
    gt_mask = np.zeros((size, size), dtype=np.uint8)

    # Georeferencing metadata: UTM Zone 32N, 10m pixel size
    transform = from_origin(500000.0, 5200000.0, 10.0, 10.0)
    crs = CRS.from_epsg(32632)

    if use_case == "deforestation":
        # Base: dense healthy forest
        # High NIR, low Red -> high NDVI (~0.75)
        before[0] = 0.09 + blur_noise[0]  # Green
        before[1] = 0.05 + blur_noise[1]  # Red
        before[2] = 0.58 + blur_noise[2]  # NIR
        before[3] = 0.14 + blur_noise[3]  # SWIR1
        before[4] = 0.06 + blur_noise[4]  # SWIR2

        after[:] = before.copy()

        # Deforested patch: irregular circular/elliptical clearings
        r1 = ((x - (cx - 60)) ** 2) / (70 ** 2) + ((y - (cy - 40)) ** 2) / (60 ** 2) <= 1.0
        r2 = ((x - (cx + 80)) ** 2) / (50 ** 2) + ((y - (cy + 70)) ** 2) / (80 ** 2) <= 1.0
        r3 = (np.abs(x - cx) < 20) & (np.abs(y - cy) < 110)  # logging road corridor
        changed = r1 | r2 | r3
        gt_mask[changed] = 1

        # In deforested patch: NIR drops sharply, Red and SWIR rise (bare soil)
        after[0, changed] = 0.16 + blur_noise[0, changed]
        after[1, changed] = 0.24 + blur_noise[1, changed]
        after[2, changed] = 0.15 + blur_noise[2, changed]
        after[3, changed] = 0.32 + blur_noise[3, changed]
        after[4, changed] = 0.22 + blur_noise[4, changed]

    elif use_case == "water":
        # Base: land with a large reservoir/lake
        # Land: moderate NIR, low water index
        before[0] = 0.12 + blur_noise[0]  # Green
        before[1] = 0.15 + blur_noise[1]  # Red
        before[2] = 0.38 + blur_noise[2]  # NIR
        before[3] = 0.22 + blur_noise[3]  # SWIR1
        before[4] = 0.12 + blur_noise[4]  # SWIR2

        # Lake region in before image
        lake_dist = np.sqrt(((x - cx) / 1.4) ** 2 + ((y - cy) / 0.9) ** 2)
        initial_water = lake_dist <= 150

        before[0, initial_water] = 0.22  # Green
        before[1, initial_water] = 0.06  # Red
        before[2, initial_water] = 0.02  # NIR
        before[3, initial_water] = 0.01  # SWIR1
        before[4, initial_water] = 0.01  # SWIR2

        after[:] = before.copy()

        # Shrunk lake: water recedes inward, outer ring becomes dry land (water loss)
        shrunk_water = lake_dist <= 85
        lost_water = initial_water & (~shrunk_water)
        gt_mask[lost_water] = 1

        # Exposed lakebed / dry sediment
        after[0, lost_water] = 0.18 + blur_noise[0, lost_water]
        after[1, lost_water] = 0.22 + blur_noise[1, lost_water]
        after[2, lost_water] = 0.30 + blur_noise[2, lost_water]
        after[3, lost_water] = 0.35 + blur_noise[3, lost_water]
        after[4, lost_water] = 0.25 + blur_noise[4, lost_water]

    elif use_case == "burn_scars":
        # Base: forest/grassland
        before[0] = 0.08 + blur_noise[0]  # Green
        before[1] = 0.06 + blur_noise[1]  # Red
        before[2] = 0.55 + blur_noise[2]  # NIR
        before[3] = 0.16 + blur_noise[3]  # SWIR1
        before[4] = 0.07 + blur_noise[4]  # SWIR2

        after[:] = before.copy()

        # Wildfire burn perimeter
        burn_zone = ((x - cx) ** 2) / (120 ** 2) + ((y - cy) ** 2) / (90 ** 2) <= 1.0
        # Add irregular ragged edge using high-frequency noise
        ragged = cv2.GaussianBlur(np.random.normal(0, 1, (size, size)), (9, 9), 0) > 0.3
        burned = burn_zone & ragged
        gt_mask[burned] = 1

        # Burn scar: severe drop in NIR, sharp rise in SWIR2 (charcoal / ash)
        after[0, burned] = 0.05 + blur_noise[0, burned]
        after[1, burned] = 0.08 + blur_noise[1, burned]
        after[2, burned] = 0.10 + blur_noise[2, burned]
        after[3, burned] = 0.38 + blur_noise[3, burned]
        after[4, burned] = 0.44 + blur_noise[4, burned]

    elif use_case == "urbanization":
        # Base: agricultural fields / green open space
        before[0] = 0.10 + blur_noise[0]  # Green
        before[1] = 0.08 + blur_noise[1]  # Red
        before[2] = 0.45 + blur_noise[2]  # NIR
        before[3] = 0.15 + blur_noise[3]  # SWIR1
        before[4] = 0.08 + blur_noise[4]  # SWIR2

        after[:] = before.copy()

        # Grid of new urban buildings, roads, and concrete developments
        urban_mask = np.zeros((size, size), dtype=bool)
        # Rectangular commercial / residential zones
        urban_mask[120:230, 140:320] = True
        urban_mask[280:400, 200:360] = True
        urban_mask[220:250, 100:420] = True  # highway
        gt_mask[urban_mask] = 1

        # Built-up: high SWIR1, lower NIR, higher Red
        after[0, urban_mask] = 0.18 + blur_noise[0, urban_mask]
        after[1, urban_mask] = 0.22 + blur_noise[1, urban_mask]
        after[2, urban_mask] = 0.19 + blur_noise[2, urban_mask]
        after[3, urban_mask] = 0.40 + blur_noise[3, urban_mask]
        after[4, urban_mask] = 0.28 + blur_noise[4, urban_mask]

    else:
        raise ValueError(f"Unknown use case: {use_case}")

    # Clip bands to valid physical reflectance range [0.0, 1.0]
    before = np.clip(before, 0.001, 0.999)
    after = np.clip(after, 0.001, 0.999)

    before_path = raw_dir / "before.tif"
    after_path = raw_dir / "after.tif"
    gt_path = gt_dir / "ground_truth.png"

    # Write multi-band GeoTIFFs using rasterio
    meta = {
        "driver": "GTiff",
        "height": size,
        "width": size,
        "count": 5,
        "dtype": "float32",
        "crs": crs,
        "transform": transform,
        "nodata": -9999.0
    }

    with rasterio.open(str(before_path), "w", **meta) as dst:
        dst.write(before)

    with rasterio.open(str(after_path), "w", **meta) as dst:
        dst.write(after)

    # Save ground truth mask as PNG (0 and 255)
    save_png((gt_mask * 255).astype(np.uint8), str(gt_path))

    return {
        "before_path": str(before_path),
        "after_path": str(after_path),
        "ground_truth_path": str(gt_path)
    }

