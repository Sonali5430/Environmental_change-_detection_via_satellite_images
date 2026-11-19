"""Image co-registration and spatial alignment module."""

from typing import Any, Dict, Tuple
import numpy as np
import cv2
import rasterio
from rasterio.warp import reproject, Resampling
from .utils import normalize_to_uint8


def align_pair(
    before_info: Dict[str, Any],
    after_info: Dict[str, Any]
) -> Tuple[np.ndarray, str]:
    """Align the after image to match the before image's grid and geometry.

    Uses rasterio.warp.reproject for georeferenced GeoTIFFs,
    and OpenCV ORB + RANSAC homography registration for plain RGB/PNG images.

    Returns:
      (aligned_after_bands, log_message)
    """
    before_bands = before_info["bands"]
    after_bands = after_info["bands"]

    is_georef = before_info.get("is_georeferenced", False) and after_info.get("is_georeferenced", False)

    # 1. Georeferenced path via rasterio
    if is_georef:
        src_crs = after_info.get("crs")
        dst_crs = before_info.get("crs")
        src_trans = after_info.get("transform")
        dst_trans = before_info.get("transform")

        if (
            src_crs == dst_crs
            and src_trans == dst_trans
            and before_bands.shape[1:] == after_bands.shape[1:]
        ):
            return after_bands.copy(), "Geospatial coordinate grid already identical."

        # Reproject after_bands to match before's grid
        c_after, _, _ = after_bands.shape
        _, h_before, w_before = before_bands.shape

        aligned = np.zeros((c_after, h_before, w_before), dtype=np.float32)

        for b in range(c_after):
            reproject(
                source=after_bands[b],
                destination=aligned[b],
                src_transform=src_trans,
                src_crs=src_crs,
                dst_transform=dst_trans,
                dst_crs=dst_crs,
                resampling=Resampling.bilinear
            )

        log_msg = f"Georeferenced alignment: reprojected {c_after} bands to {dst_crs} ({w_before}x{h_before})."
        return aligned, log_msg

    # 2. Non-georeferenced path (Standard RGB / PNG)
    _, h1, w1 = before_bands.shape
    c2, h2, w2 = after_bands.shape

    # If shapes differ, first resize after to (h1, w1)
    if (h1, w1) != (h2, w2):
        resized_after = np.zeros((c2, h1, w1), dtype=np.float32)
        for b in range(c2):
            resized_after[b] = cv2.resize(after_bands[b], (w1, h1), interpolation=cv2.INTER_LINEAR)
        after_bands = resized_after

    # Compute single-channel representations for feature matching
    if before_bands.shape[0] >= 3:
        # Convert RGB to grayscale
        gray1 = cv2.cvtColor(normalize_to_uint8(before_bands[:3]), cv2.COLOR_RGB2GRAY)
    else:
        gray1 = normalize_to_uint8(before_bands[0])

    if after_bands.shape[0] >= 3:
        gray2 = cv2.cvtColor(normalize_to_uint8(after_bands[:3]), cv2.COLOR_RGB2GRAY)
    else:
        gray2 = normalize_to_uint8(after_bands[0])

    # ORB feature detector and descriptor extractor
    orb = cv2.ORB_create(nfeatures=2500)
    kp1, des1 = orb.detectAndCompute(gray1, None)
    kp2, des2 = orb.detectAndCompute(gray2, None)

    if des1 is not None and des2 is not None and len(kp1) >= 8 and len(kp2) >= 8:
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des2, des1)

        # Sort matches by hamming distance
        matches = sorted(matches, key=lambda m: m.distance)
        good_matches = matches[: min(len(matches), 300)]

        if len(good_matches) >= 8:
            pts2 = np.float32([kp2[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            pts1 = np.float32([kp1[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

            # Find homography using RANSAC
            H, inliers = cv2.findHomography(pts2, pts1, cv2.RANSAC, 5.0)

            if H is not None and inliers is not None and np.sum(inliers) >= 8:
                aligned = np.zeros_like(after_bands, dtype=np.float32)
                for b in range(c2):
                    aligned[b] = cv2.warpPerspective(
                        after_bands[b],
                        H,
                        (w1, h1),
                        flags=cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_REFLECT_101
                    )
                inlier_count = int(np.sum(inliers))
                log_msg = f"Feature registration: aligned with ORB + RANSAC homography ({inlier_count} inliers)."
                return aligned, log_msg

    # Fallback if feature matching doesn't find strong homography
    return after_bands.copy(), "Spatial alignment: dimensions matched via bilinear interpolation."
