"""Script to generate all 5 educational Jupyter notebooks for the DIP project."""

import json
from pathlib import Path


def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.11"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }


def md_cell(source_text):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source_text.strip().split("\n")]
    }


def code_cell(source_code):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source_code.strip().split("\n")]
    }


def generate_all_notebooks(dest_dirs):
    # =========================================================================
    # NOTEBOOK 01: DATA EXPLORATION
    # =========================================================================
    nb01_cells = [
        md_cell("""# 01. Satellite Data Exploration & Multi-spectral Band Inspection
### Project: Image Change Detection using Digital Image Processing for Environmental Monitoring

This notebook demonstrates:
1. Loading multi-band Sentinel-2 L2A GeoTIFFs (B03 Green, B04 Red, B08 NIR, B11 SWIR1, B12 SWIR2) and plain RGB images.
2. Inspecting spatial georeferencing, affine transformation, and coordinate reference systems (CRS).
3. Visualizing individual spectral reflectance bands using Matplotlib.
4. Rendering **Natural Color (RGB)** and **False Color Infrared (NIR-R-G)** composite views.
5. Analyzing spectral reflectance distributions using multi-band histograms."""),
        code_cell("""import sys
import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# Connect to modular backend services
sys.path.append(str(Path.cwd().parent / "backend"))

from app.services.utils import load_image, generate_synthetic_pair, pixel_area_m2, normalize_to_uint8
from app.services.indices import USE_CASES"""),
        md_cell("""### Step 1: Ensure Dataset Availability
If real Copernicus Analytical GeoTIFF downloads are not present, generate realistic synthetic pairs for testing."""),
        code_cell("""project_root = Path.cwd().parent
use_case = "deforestation"

# Generate or verify synthetic dataset
pair_paths = generate_synthetic_pair(use_case=use_case, size=512, base_dir=str(project_root))
before_path = pair_paths["before_path"]
after_path = pair_paths["after_path"]
gt_path = pair_paths["ground_truth_path"]

print(f"Before Image Path: {before_path}")
print(f"After Image Path:  {after_path}")
print(f"Ground Truth Path: {gt_path}")"""),
        md_cell("""### Step 2: Load Multi-Spectral Imagery & Inspect Geospatial Metadata"""),
        code_cell("""before_info = load_image(before_path)
after_info = load_image(after_path)

print("=" * 55)
print("SATELLITE SCENE METADATA")
print("=" * 55)
print(f"Array Shape (C, H, W): {before_info['shape']}")
print(f"Multispectral (>=4 bands): {before_info['is_multispectral']}")
print(f"Georeferenced: {before_info['is_georeferenced']}")
print(f"Coordinate Reference System (CRS): {before_info['crs']}")
print(f"Affine Transform:\n{before_info['transform']}")

px_area = pixel_area_m2(before_info['transform'], before_info['crs'])
print(f"Ground Pixel Area: {px_area:.2f} m^2 (Equivalent to {np.sqrt(px_area):.1f}m spatial resolution)")"""),
        md_cell("""### Step 3: Inspect Individual Spectral Bands
Sentinel-2 Band Configuration:
- **Band 0**: B03 (Green - 560 nm)
- **Band 1**: B04 (Red - 665 nm)
- **Band 2**: B08 (Near-Infrared / NIR - 842 nm)
- **Band 3**: B11 (Short-Wave Infrared 1 / SWIR1 - 1610 nm)
- **Band 4**: B12 (Short-Wave Infrared 2 / SWIR2 - 2190 nm)"""),
        code_cell("""band_labels = [
    "B03 (Green)", "B04 (Red)", "B08 (NIR)",
    "B11 (SWIR1)", "B12 (SWIR2)"
]

fig, axes = plt.subplots(1, 5, figsize=(20, 4))
for i in range(5):
    im = axes[i].imshow(before_info["bands"][i], cmap="viridis")
    axes[i].set_title(band_labels[i], fontsize=12, fontweight="bold")
    axes[i].axis("off")
    fig.colorbar(im, ax=axes[i], fraction=0.046, pad=0.04)

plt.suptitle("Sentinel-2 Individual Spectral Bands (Surface Reflectance)", fontsize=15, y=1.05)
plt.tight_layout()
plt.show()"""),
        md_cell("""### Step 4: True Color vs False Color Infrared Composites
In remote sensing, **False Color Infrared (NIR -> Red, Red -> Green, Green -> Blue)** makes healthy chlorophyll-rich vegetation glow in bright red, making forest disturbance instantly detectable."""),
        code_cell("""bands = before_info["bands"]

# Natural Color: Red=B04 (index 1), Green=B03 (index 0), Blue=B03*0.85
natural_rgb = np.stack([
    normalize_to_uint8(bands[1]),
    normalize_to_uint8(bands[0]),
    normalize_to_uint8(bands[0] * 0.85)
], axis=-1)

# False Color Infrared: Red=B08 (NIR), Green=B04 (Red), Blue=B03 (Green)
false_color_ir = np.stack([
    normalize_to_uint8(bands[2]),
    normalize_to_uint8(bands[1]),
    normalize_to_uint8(bands[0])
], axis=-1)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
axes[0].imshow(natural_rgb)
axes[0].set_title("Natural Color Composite (RGB)", fontsize=13, fontweight="bold")
axes[0].axis("off")

axes[1].imshow(false_color_ir)
axes[1].set_title("False Color Infrared (NIR-Red-Green)\n[Bright Red = Dense Canopy]", fontsize=13, fontweight="bold")
axes[1].axis("off")

plt.tight_layout()
plt.show()"""),
        md_cell("""### Step 5: Spectral Reflectance Histograms"""),
        code_cell("""plt.figure(figsize=(10, 5))
colors = ["green", "red", "darkred", "purple", "brown"]

for i in range(5):
    plt.hist(
        before_info["bands"][i].ravel(),
        bins=60,
        range=(0.0, 0.8),
        color=colors[i],
        alpha=0.5,
        label=band_labels[i]
    )

plt.title("Spectral Reflectance Distribution per Band", fontsize=13, fontweight="bold")
plt.xlabel("Reflectance Value [0.0 - 1.0]", fontsize=11)
plt.ylabel("Pixel Frequency", fontsize=11)
plt.legend(frameon=True)
plt.grid(True, linestyle="--", alpha=0.5)
plt.show()""")
    ]

    # =========================================================================
    # NOTEBOOK 02: PREPROCESSING
    # =========================================================================
    nb02_cells = [
        md_cell("""# 02. Image Preprocessing, Denoising & Co-Registration
### Project: Image Change Detection using Digital Image Processing for Environmental Monitoring

This notebook demonstrates:
1. Spatial noise reduction using **Gaussian Blur** vs **Median Filtering**.
2. **Radiometric Normalization** via Histogram Matching to eliminate seasonal illumination and atmospheric discrepancies.
3. Automated **Cloud and Bright Haze Masking**.
4. Multi-temporal image **Co-Registration**:
   - Georeferenced scenes: `rasterio.warp.reproject`
   - Unreferenced RGB scenes: OpenCV **ORB** feature detection + **RANSAC** homography alignment."""),
        code_cell("""import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(str(Path.cwd().parent / "backend"))

from app.services.utils import load_image, generate_synthetic_pair, normalize_to_uint8
from app.services.preprocessing import denoise, histogram_match, cloud_mask, preprocess_pair
from app.services.registration import align_pair"""),
        md_cell("""### Step 1: Load Image Pair"""),
        code_cell("""project_root = Path.cwd().parent
pair_paths = generate_synthetic_pair("deforestation", size=512, base_dir=str(project_root))

before_info = load_image(pair_paths["before_path"])
after_info = load_image(pair_paths["after_path"])

print(f"Loaded Before Shape: {before_info['shape']}")
print(f"Loaded After Shape:  {after_info['shape']}")"""),
        md_cell("""### Step 2: Denoising Algorithms Comparison
We compare Gaussian smoothing ($k=5$) against Median filtering on noisy satellite channels."""),
        code_cell("""noisy_sample = before_info["bands"][2].copy()  # NIR band

# Denoising
gauss_denoised = denoise(noisy_sample, method="gaussian", ksize=5)
median_denoised = denoise(noisy_sample, method="median", ksize=5)

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
axes[0].imshow(noisy_sample, cmap="viridis")
axes[0].set_title("Original NIR Band", fontsize=12, fontweight="bold")
axes[0].axis("off")

axes[1].imshow(gauss_denoised, cmap="viridis")
axes[1].set_title("Gaussian Filter (k=5)", fontsize=12, fontweight="bold")
axes[1].axis("off")

axes[2].imshow(median_denoised, cmap="viridis")
axes[2].set_title("Median Filter (k=5)", fontsize=12, fontweight="bold")
axes[2].axis("off")

plt.tight_layout()
plt.show()"""),
        md_cell("""### Step 3: Radiometric Calibration via Histogram Matching
Different acquisition dates have varying sun angles, atmospheric haze, and soil moisture. Histogram matching calibrates the target image's histogram to match the reference image."""),
        code_cell("""# Add synthetic atmospheric shift to after image
shifted_after = after_info["bands"] * 1.25 + 0.04
matched_after = histogram_match(shifted_after, before_info["bands"])

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Before NIR
axes[0, 0].imshow(before_info["bands"][2], cmap="viridis")
axes[0, 0].set_title("Reference (Before NIR)", fontweight="bold")
axes[0, 0].axis("off")

# Uncalibrated After NIR
axes[0, 1].imshow(shifted_after[2], cmap="viridis")
axes[0, 1].set_title("Uncalibrated (After NIR)", fontweight="bold")
axes[0, 1].axis("off")

# Histogram before matching
axes[1, 0].hist(before_info["bands"][2].ravel(), bins=50, color="blue", alpha=0.6, label="Reference")
axes[1, 0].hist(shifted_after[2].ravel(), bins=50, color="orange", alpha=0.5, label="Uncalibrated")
axes[1, 0].set_title("Before Histogram Matching", fontweight="bold")
axes[1, 0].legend()
axes[1, 0].grid(True, linestyle="--", alpha=0.5)

# Histogram after matching
axes[1, 1].hist(before_info["bands"][2].ravel(), bins=50, color="blue", alpha=0.6, label="Reference")
axes[1, 1].hist(matched_after[2].ravel(), bins=50, color="green", alpha=0.5, label="Matched After")
axes[1, 1].set_title("After Histogram Matching (Radiometrically Calibrated)", fontweight="bold")
axes[1, 1].legend()
axes[1, 1].grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
plt.show()"""),
        md_cell("""### Step 4: Spatial Co-Registration & Alignment"""),
        code_cell("""aligned_after, reg_msg = align_pair(before_info, after_info)
print(f"Registration Output: {reg_msg}")
print(f"Aligned Array Shape: {aligned_after.shape}")"""),
        md_cell("""### Step 5: Full Automated Preprocessing Pipeline"""),
        code_cell("""clean_before, clean_after, valid_mask = preprocess_pair(
    before_info["bands"],
    aligned_after,
    do_denoise=True,
    do_match=True
)

print(f"Cleaned Before Shape: {clean_before.shape}")
print(f"Cleaned After Shape:  {clean_after.shape}")
print(f"Valid Pixels Percentage: {valid_mask.mean() * 100:.2f}%")""")
    ]

    # =========================================================================
    # NOTEBOOK 03: INDICES
    # =========================================================================
    nb03_cells = [
        md_cell("""# 03. Spectral Environmental Indices Computation
### Project: Image Change Detection using Digital Image Processing for Environmental Monitoring

This notebook demonstrates:
1. Mathematical implementation of 4 key environmental indices:
   - **NDVI** (Normalized Difference Vegetation Index): $\\frac{NIR - Red}{NIR + Red}$
   - **NDWI** (Normalized Difference Water Index): $\\frac{Green - NIR}{Green + NIR}$
   - **NBR** (Normalized Burn Ratio): $\\frac{NIR - SWIR2}{NIR + SWIR2}$
   - **NDBI** (Normalized Difference Built-up Index): $\\frac{SWIR1 - NIR}{SWIR1 + NIR}$
2. Colormap visualization highlighting physical ecological features.
3. Index differencing ($\Delta Index = Index_{after} - Index_{before}$) to pinpoint environmental change."""),
        code_cell("""import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(str(Path.cwd().parent / "backend"))

from app.services.utils import load_image, generate_synthetic_pair
from app.services.indices import ndvi, ndwi, nbr, ndbi, compute_index, USE_CASES"""),
        md_cell("""### Step 1: Compute & Visualize NDVI (Deforestation & Forest Cover)"""),
        code_cell("""project_root = Path.cwd().parent
pair_deforest = generate_synthetic_pair("deforestation", size=512, base_dir=str(project_root))

b_info = load_image(pair_deforest["before_path"])
a_info = load_image(pair_deforest["after_path"])

ndvi_before = compute_index(b_info["bands"], "deforestation")
ndvi_after = compute_index(a_info["bands"], "deforestation")
ndvi_diff = ndvi_after - ndvi_before

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
im0 = axes[0].imshow(ndvi_before, cmap="YlGn", vmin=-0.2, vmax=1.0)
axes[0].set_title("NDVI Before (Dense Forest)", fontweight="bold")
axes[0].axis("off")
fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)

im1 = axes[1].imshow(ndvi_after, cmap="YlGn", vmin=-0.2, vmax=1.0)
axes[1].set_title("NDVI After (Deforested Clearings)", fontweight="bold")
axes[1].axis("off")
fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)

im2 = axes[2].imshow(ndvi_diff, cmap="RdYlGn", vmin=-1.0, vmax=0.2)
axes[2].set_title("Delta NDVI (Red = Severe Vegetation Loss)", fontweight="bold")
axes[2].axis("off")
fig.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)

plt.suptitle("Deforestation Monitoring via NDVI", fontsize=15, y=1.03)
plt.tight_layout()
plt.show()"""),
        md_cell("""### Step 2: Compute & Visualize NDWI (Water Body Shrinking)"""),
        code_cell("""pair_water = generate_synthetic_pair("water", size=512, base_dir=str(project_root))
b_water = load_image(pair_water["before_path"])
a_water = load_image(pair_water["after_path"])

ndwi_before = compute_index(b_water["bands"], "water")
ndwi_after = compute_index(a_water["bands"], "water")
ndwi_diff = ndwi_after - ndwi_before

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
im0 = axes[0].imshow(ndwi_before, cmap="Blues", vmin=-0.8, vmax=1.0)
axes[0].set_title("NDWI Before (Full Reservoir)", fontweight="bold")
axes[0].axis("off")
fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)

im1 = axes[1].imshow(ndwi_after, cmap="Blues", vmin=-0.8, vmax=1.0)
axes[1].set_title("NDWI After (Shrunk Reservoir)", fontweight="bold")
axes[1].axis("off")
fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)

im2 = axes[2].imshow(ndwi_diff, cmap="coolwarm", vmin=-1.0, vmax=1.0)
axes[2].set_title("Delta NDWI (Blue = Water Gain, Red = Water Loss)", fontweight="bold")
axes[2].axis("off")
fig.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)

plt.suptitle("Hydrological Monitoring via NDWI", fontsize=15, y=1.03)
plt.tight_layout()
plt.show()"""),
        md_cell("""### Step 3: Compute & Visualize NBR (Wildfire Burn Scars)"""),
        code_cell("""pair_burn = generate_synthetic_pair("burn_scars", size=512, base_dir=str(project_root))
b_burn = load_image(pair_burn["before_path"])
a_burn = load_image(pair_burn["after_path"])

nbr_before = compute_index(b_burn["bands"], "burn_scars")
nbr_after = compute_index(a_burn["bands"], "burn_scars")
dnbr = nbr_before - nbr_after  # Delta NBR: higher drop indicates higher burn severity

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
im0 = axes[0].imshow(nbr_before, cmap="YlOrRd_r", vmin=-0.5, vmax=1.0)
axes[0].set_title("NBR Pre-Fire", fontweight="bold")
axes[0].axis("off")
fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)

im1 = axes[1].imshow(nbr_after, cmap="YlOrRd_r", vmin=-0.5, vmax=1.0)
axes[1].set_title("NBR Post-Fire (Burn Scar)", fontweight="bold")
axes[1].axis("off")
fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)

im2 = axes[2].imshow(dnbr, cmap="hot_r", vmin=0.0, vmax=1.5)
axes[2].set_title("Delta NBR Burn Severity", fontweight="bold")
axes[2].axis("off")
fig.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)

plt.suptitle("Wildfire Burn Severity via NBR", fontsize=15, y=1.03)
plt.tight_layout()
plt.show()"""),
        md_cell("""### Step 4: Compute & Visualize NDBI (Urbanization & Built-up Sprawl)"""),
        code_cell("""pair_urban = generate_synthetic_pair("urbanization", size=512, base_dir=str(project_root))
b_urban = load_image(pair_urban["before_path"])
a_urban = load_image(pair_urban["after_path"])

ndbi_before = compute_index(b_urban["bands"], "urbanization")
ndbi_after = compute_index(a_urban["bands"], "urbanization")
ndbi_diff = ndbi_after - ndbi_before

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
im0 = axes[0].imshow(ndbi_before, cmap="Purples", vmin=-0.8, vmax=0.6)
axes[0].set_title("NDBI Before (Rural Open Fields)", fontweight="bold")
axes[0].axis("off")
fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)

im1 = axes[1].imshow(ndbi_after, cmap="Purples", vmin=-0.8, vmax=0.6)
axes[1].set_title("NDBI After (New Urban Construction)", fontweight="bold")
axes[1].axis("off")
fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)

im2 = axes[2].imshow(ndbi_diff, cmap="magma", vmin=0.0, vmax=1.0)
axes[2].set_title("Delta NDBI (Built-up Gain)", fontweight="bold")
axes[2].axis("off")
fig.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)

plt.suptitle("Urban Sprawl Monitoring via NDBI", fontsize=15, y=1.03)
plt.tight_layout()
plt.show()""")
    ]

    # =========================================================================
    # NOTEBOOK 04: CHANGE DETECTION
    # =========================================================================
    nb04_cells = [
        md_cell("""# 04. Digital Image Processing Change Detection Algorithms
### Project: Image Change Detection using Digital Image Processing for Environmental Monitoring

This notebook demonstrates:
1. Execution of 5 classical DIP change detection methods:
   - **Index Differencing**
   - **Image Differencing**
   - **PCA Differencing** (Principal Component Analysis on stacked spectral delta vectors)
   - **Change Vector Analysis** (CVA Euclidean magnitude)
   - **Structural Similarity** (1 - SSIM dissimilarity)
2. Thresholding strategies (**Otsu** vs **Adaptive Gaussian**).
3. Postprocessing: **Morphological Opening & Closing** + **Small region area filtering**.
4. Directional **Gain vs Loss** environmental classification.
5. Generating high-contrast **alpha-blended overlays**."""),
        code_cell("""import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(str(Path.cwd().parent / "backend"))

from app.services.utils import load_image, generate_synthetic_pair, normalize_to_uint8
from app.services.preprocessing import preprocess_pair
from app.services.change_detection import run_method
from app.services.postprocessing import (
    morphological_cleanup,
    remove_small_regions,
    classify_gain_loss,
    make_overlay,
    compute_statistics
)"""),
        md_cell("""### Step 1: Prepare Preprocessed Image Pair"""),
        code_cell("""project_root = Path.cwd().parent
pair_paths = generate_synthetic_pair("deforestation", size=512, base_dir=str(project_root))

before_info = load_image(pair_paths["before_path"])
after_info = load_image(pair_paths["after_path"])

clean_before, clean_after, valid_mask = preprocess_pair(
    before_info["bands"], after_info["bands"], do_denoise=True, do_match=True
)

print("Preprocessed pair ready.")"""),
        md_cell("""### Step 2: Compare Continuous Difference Maps Across All 5 Algorithms"""),
        code_cell("""methods = ["index_differencing", "image_differencing", "pca", "cva", "ssim"]
results = {}

fig, axes = plt.subplots(1, 5, figsize=(22, 4))
for i, m in enumerate(methods):
    res = run_method(m, clean_before, clean_after, use_case="deforestation", is_multispectral=True)
    results[m] = res
    im = axes[i].imshow(res["diff_map"], cmap="magma")
    axes[i].set_title(m.replace("_", " ").title(), fontsize=11, fontweight="bold")
    axes[i].axis("off")
    fig.colorbar(im, ax=axes[i], fraction=0.046, pad=0.04)

plt.suptitle("Comparison of Raw Difference Maps", fontsize=15, y=1.05)
plt.tight_layout()
plt.show()"""),
        md_cell("""### Step 3: Thresholding & Morphological Cleanup Pipeline
We demonstrate how morphological opening and small region filtering eliminate isolated false alarms."""),
        code_cell("""raw_mask = results["pca"]["mask"]
clean_morph = morphological_cleanup(raw_mask, ksize=5)
final_filtered = remove_small_regions(clean_morph, min_area=40)

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
axes[0].imshow(raw_mask, cmap="gray")
axes[0].set_title("1. Raw Otsu Segmented Mask", fontweight="bold")
axes[0].axis("off")

axes[1].imshow(clean_morph, cmap="gray")
axes[1].set_title("2. Morphological Cleanup (Opening + Closing)", fontweight="bold")
axes[1].axis("off")

axes[2].imshow(final_filtered, cmap="gray")
axes[2].set_title("3. Filtered Mask (Removed Regions < 40 px)", fontweight="bold")
axes[2].axis("off")

plt.tight_layout()
plt.show()"""),
        md_cell("""### Step 4: Directional Gain vs Loss Classification & Quantitative Statistics"""),
        code_cell("""gain_mask, loss_mask = classify_gain_loss(
    results["pca"]["signed_diff"],
    final_filtered,
    use_case="deforestation"
)

stats = compute_statistics(
    mask=final_filtered,
    signed_diff=results["pca"]["signed_diff"],
    pixel_area_m2=100.0,
    use_case="deforestation"
)

print("=" * 45)
print("STATISTICAL CHANGE SUMMARY")
print("=" * 45)
for k, v in stats.items():
    print(f"{k:<18}: {v}")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].imshow(loss_mask, cmap="Reds")
axes[0].set_title(f"Vegetation Loss ({stats['loss_km2']} km^2)", fontweight="bold", color="darkred")
axes[0].axis("off")

axes[1].imshow(gain_mask, cmap="Greens")
axes[1].set_title(f"Vegetation Gain ({stats['gain_km2']} km^2)", fontweight="bold", color="darkgreen")
axes[1].axis("off")

plt.tight_layout()
plt.show()"""),
        md_cell("""### Step 5: Semi-Transparent Overlay Generation"""),
        code_cell("""overlay_img = make_overlay(clean_after, final_filtered, color=(239, 68, 68), alpha=0.5)

plt.figure(figsize=(8, 8))
plt.imshow(overlay_img)
plt.title(f"Deforestation Change Overlay ({stats['percent_change']}% Changed Area)", fontsize=13, fontweight="bold")
plt.axis("off")
plt.show()""")
    ]

    # =========================================================================
    # NOTEBOOK 05: EVALUATION
    # =========================================================================
    nb05_cells = [
        md_cell("""# 05. Quantitative Evaluation & Comparative Benchmarking
### Project: Image Change Detection using Digital Image Processing for Environmental Monitoring

This notebook demonstrates:
1. Ground truth verification metrics:
   - **Precision**: $\\frac{TP}{TP + FP}$
   - **Recall**: $\\frac{TP}{TP + FN}$
   - **F1-Score**: $2 \\cdot \\frac{P \\cdot R}{P + R}$
   - **IoU** (Intersection over Union / Jaccard Index): $\\frac{TP}{TP + FP + FN}$
   - **Overall Accuracy**: $\\frac{TP + TN}{Total}$
2. Multi-method benchmark comparison table.
3. Comparative visualization bar charts.
4. Optional **Random Forest Machine Learning baseline** for pixel classification."""),
        code_cell("""import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(str(Path.cwd().parent / "backend"))

from app.services.utils import load_image, generate_synthetic_pair
from app.services.preprocessing import preprocess_pair
from app.services.evaluation import compute_metrics, compare_methods, random_forest_baseline"""),
        md_cell("""### Step 1: Load Image Pair & Ground Truth Mask"""),
        code_cell("""project_root = Path.cwd().parent
pair_paths = generate_synthetic_pair("deforestation", size=512, base_dir=str(project_root))

before_info = load_image(pair_paths["before_path"])
after_info = load_image(pair_paths["after_path"])
gt_info = load_image(pair_paths["ground_truth_path"])

clean_before, clean_after, _ = preprocess_pair(
    before_info["bands"], after_info["bands"], do_denoise=True, do_match=True
)

gt_mask = (gt_info["bands"][0] > 0).astype(int)
print(f"Ground Truth Change Pixels: {np.count_nonzero(gt_mask)} ({np.mean(gt_mask)*100:.2f}% of scene)")"""),
        md_cell("""### Step 2: Multi-Method DIP Benchmark Comparison"""),
        code_cell("""comparison = compare_methods(
    before_bands=clean_before,
    after_bands=clean_after,
    use_case="deforestation",
    is_multispectral=True,
    ground_truth=gt_mask,
    threshold_mode="otsu",
    min_area=30
)

print(f"Best Performing DIP Method: {comparison['best_method']}")
print("\n" + "=" * 75)
print(f"{'Method':<22} | {'Precision':<9} | {'Recall':<9} | {'F1-Score':<9} | {'IoU':<9} | {'Accuracy':<9}")
print("=" * 75)
for row in comparison["metrics_table"]:
    print(f"{row['method']:<22} | {row['precision']:<9.4f} | {row['recall']:<9.4f} | {row['f1_score']:<9.4f} | {row['iou']:<9.4f} | {row['accuracy']:<9.4f}")
print("=" * 75)"""),
        md_cell("""### Step 3: Comparative Performance Bar Chart"""),
        code_cell("""metrics_table = comparison["metrics_table"]
method_names = [m["method"].replace("_", " ").title() for m in metrics_table]
f1_scores = [m["f1_score"] for m in metrics_table]
ious = [m["iou"] for m in metrics_table]
recalls = [m["recall"] for m in metrics_table]
precisions = [m["precision"] for m in metrics_table]

x = np.arange(len(method_names))
width = 0.2

plt.figure(figsize=(13, 6))
plt.bar(x - 1.5 * width, precisions, width, label="Precision", color="#3b82f6")
plt.bar(x - 0.5 * width, recalls, width, label="Recall", color="#10b981")
plt.bar(x + 0.5 * width, f1_scores, width, label="F1-Score", color="#f59e0b")
plt.bar(x + 1.5 * width, ious, width, label="IoU", color="#ef4444")

plt.xticks(x, method_names, fontsize=11, fontweight="bold")
plt.ylabel("Score [0.0 - 1.0]", fontsize=12)
plt.title("Comparative Performance across DIP Change Detection Methods", fontsize=14, fontweight="bold")
plt.legend(frameon=True, fontsize=11)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.ylim(0.0, 1.05)
plt.tight_layout()
plt.show()"""),
        md_cell("""### Step 4: Optional Machine Learning Benchmark (Random Forest)
A Random Forest pixel classifier trained on spectral differences, spectral index shift, SSIM, and spatial Laplacian gradients serves as an ML baseline against classical DIP techniques."""),
        code_cell("""rf_result = random_forest_baseline(
    before_bands=clean_before,
    after_bands=clean_after,
    ground_truth=gt_mask,
    use_case="deforestation",
    train_ratio=0.25
)

print("=" * 45)
print("RANDOM FOREST ML BASELINE METRICS")
print("=" * 45)
for k, v in rf_result["metrics"].items():
    if isinstance(v, float):
        print(f"{k:<15}: {v:.4f}")

# Plot feature importances
importances = rf_result["feature_importances"]
plt.figure(figsize=(10, 4))
plt.barh(list(importances.keys()), list(importances.values()), color="#8b5cf6")
plt.xlabel("Feature Importance", fontsize=11)
plt.title("Random Forest Pixel Feature Contribution", fontsize=13, fontweight="bold")
plt.grid(axis="x", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()"""),
        md_cell("""### Step 5: Visual Detection Comparison (Ground Truth vs DIP vs ML)"""),
        code_cell("""best_dip_mask = comparison["results"][comparison["best_method"]]["mask"]
rf_mask = rf_result["mask"]

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
axes[0].imshow(gt_mask, cmap="gray")
axes[0].set_title("Ground Truth Mask", fontsize=12, fontweight="bold")
axes[0].axis("off")

axes[1].imshow(best_dip_mask, cmap="magma")
axes[1].set_title(f"Best DIP: {comparison['best_method']} (F1: {max(f1_scores):.4f})", fontsize=12, fontweight="bold")
axes[1].axis("off")

axes[2].imshow(rf_mask, cmap="magma")
axes[2].set_title(f"Random Forest ML (F1: {rf_result['metrics']['f1_score']:.4f})", fontsize=12, fontweight="bold")
axes[2].axis("off")

plt.tight_layout()
plt.show()""")
    ]

    notebook_map = {
        "01_data_exploration.ipynb": make_notebook(nb01_cells),
        "02_preprocessing.ipynb": make_notebook(nb02_cells),
        "03_indices.ipynb": make_notebook(nb03_cells),
        "04_change_detection.ipynb": make_notebook(nb04_cells),
        "05_evaluation.ipynb": make_notebook(nb05_cells),
    }

    for d in dest_dirs:
        dest_path = Path(d)
        dest_path.mkdir(parents=True, exist_ok=True)
        for fname, nb_json in notebook_map.items():
            out_file = dest_path / fname
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(nb_json, f, indent=1)
            print(f"Generated {out_file.name} ({out_file.stat().st_size} bytes) in {d}")


if __name__ == "__main__":
    dirs = [
        "C:\\CGIP_MP\\Environmental_change-_detection_via_satellite_images\\notebooks",
        "C:\\Users\\magad\\.gemini\antigravity\\scratch\\change-detection\\notebooks"
    ]
    generate_all_notebooks(dirs)
