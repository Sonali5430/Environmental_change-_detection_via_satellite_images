"""Phase 1 Verification Script.

Tests all DIP services, synthetic data generation, change detection algorithms,
metrics evaluation, and machine learning baseline.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.services.utils import (
    generate_synthetic_pair,
    load_image,
    save_png,
    normalize_to_uint8,
    pixel_area_m2
)
from app.services.preprocessing import preprocess_pair
from app.services.registration import align_pair
from app.services.indices import compute_index, USE_CASES
from app.services.change_detection import run_method
from app.services.postprocessing import (
    morphological_cleanup,
    remove_small_regions,
    make_overlay,
    compute_statistics,
    mask_to_geojson
)
from app.services.evaluation import (
    compute_metrics,
    compare_methods,
    random_forest_baseline
)


def run_phase1_verification():
    print("=" * 60)
    print("PHASE 1 VERIFICATION: Image Change Detection DIP Services")
    print("=" * 60)

    project_root = backend_dir.parent
    print(f"Project root: {project_root}")

    # 1. Test synthetic pair generation for all 4 use cases
    print("\n[Step 1] Generating synthetic data pairs for all 4 use cases...")
    use_cases = ["deforestation", "water", "burn_scars", "urbanization"]
    pairs = {}
    for uc in use_cases:
        paths = generate_synthetic_pair(uc, size=256, base_dir=str(project_root))
        pairs[uc] = paths
        print(f"  [OK] Generated {uc}: before={Path(paths['before_path']).name}, after={Path(paths['after_path']).name}, gt={Path(paths['ground_truth_path']).name}")

    # 2. Test Image Loading & Georeferencing
    print("\n[Step 2] Testing load_image & georeferencing metadata on 'deforestation'...")
    before_info = load_image(pairs["deforestation"]["before_path"])
    after_info = load_image(pairs["deforestation"]["after_path"])
    gt_info = load_image(pairs["deforestation"]["ground_truth_path"])

    print(f"  Before shape: {before_info['shape']}, Multispectral: {before_info['is_multispectral']}, Georeferenced: {before_info['is_georeferenced']}")
    print(f"  CRS: {before_info['crs']}, Transform:\n{before_info['transform']}")
    px_area = pixel_area_m2(before_info["transform"], before_info["crs"])
    print(f"  Calculated ground pixel area: {px_area:.2f} m^2")

    # 3. Test Alignment / Registration
    print("\n[Step 3] Testing align_pair...")
    aligned_after, reg_log = align_pair(before_info, after_info)
    print(f"  Registration log: {reg_log}")
    print(f"  Aligned after shape: {aligned_after.shape}")

    # 4. Test Preprocessing (Denoise, Histogram match, Cloud mask)
    print("\n[Step 4] Testing preprocess_pair...")
    clean_before, clean_after, valid_mask = preprocess_pair(
        before_info["bands"], aligned_after, do_denoise=True, do_match=True
    )
    print(f"  Valid pixels ratio: {valid_mask.mean():.4f}")

    # 5. Test Spectral Indices
    print("\n[Step 5] Testing compute_index...")
    for uc in use_cases:
        idx = compute_index(clean_before, uc)
        print(f"  Index for {uc} ({USE_CASES[uc]['index_name']}): min={idx.min():.3f}, max={idx.max():.3f}, mean={idx.mean():.3f}")

    # 6. Test Change Detection Methods Comparison & Evaluation
    print("\n[Step 6] Running compare_methods on 'deforestation' with Ground Truth...")
    gt_mask = (gt_info["bands"][0] > 0).astype(int)
    comparison = compare_methods(
        before_bands=clean_before,
        after_bands=clean_after,
        use_case="deforestation",
        is_multispectral=True,
        ground_truth=gt_mask,
        threshold_mode="otsu",
        min_area=20
    )

    print("\n" + "-" * 75)
    print(f"{'Method':<22} | {'Precision':<9} | {'Recall':<9} | {'F1-Score':<9} | {'IoU':<9} | {'Accuracy':<9}")
    print("-" * 75)
    for row in comparison["metrics_table"]:
        print(f"{row['method']:<22} | {row['precision']:<9.4f} | {row['recall']:<9.4f} | {row['f1_score']:<9.4f} | {row['iou']:<9.4f} | {row['accuracy']:<9.4f}")
    print("-" * 75)
    print(f"Best DIP Method: {comparison['best_method']}")

    # 7. Test Postprocessing: Statistics, Overlay, and GeoJSON
    print("\n[Step 7] Testing postprocessing, statistics, overlay, and GeoJSON...")
    best_res = comparison["results"][comparison["best_method"]]
    stats = compute_statistics(
        mask=best_res["mask"],
        signed_diff=best_res["signed_diff"],
        pixel_area_m2=px_area,
        use_case="deforestation"
    )
    print("  Change Statistics:")
    for k, v in stats.items():
        print(f"    - {k}: {v}")

    # Test overlay creation
    overlay = make_overlay(clean_after, best_res["mask"], color=(34, 197, 94))
    overlay_path = project_root / "results" / "deforestation" / "overlay_test.png"
    save_png(overlay, str(overlay_path))
    print(f"  [OK] Saved overlay preview to: {overlay_path.name}")

    # Test GeoJSON creation
    geojson = mask_to_geojson(best_res["mask"], transform=before_info["transform"], crs=before_info["crs"])
    print(f"  [OK] Generated GeoJSON with {len(geojson['features'])} change polygons (CRS: EPSG:4326)")

    # 8. Test Optional Random Forest ML Baseline
    print("\n[Step 8] Testing optional Random Forest baseline...")
    rf_res = random_forest_baseline(
        before_bands=clean_before,
        after_bands=clean_after,
        ground_truth=gt_mask,
        use_case="deforestation",
        train_ratio=0.25
    )
    print("  Random Forest Metrics:")
    for k in ["precision", "recall", "f1_score", "iou", "accuracy"]:
        print(f"    - {k}: {rf_res['metrics'][k]:.4f}")
    print(f"  Top Features: {rf_res['feature_importances']}")

    print("\n" + "=" * 60)
    print("ALL PHASE 1 SERVICES & PIPELINES VERIFIED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_phase1_verification()
