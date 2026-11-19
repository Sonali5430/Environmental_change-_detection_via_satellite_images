"""Evaluation module: quantitative verification metrics, multi-method comparison, and Random Forest ML baseline."""

from typing import Any, Dict, List, Optional
import numpy as np
import cv2
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from .change_detection import run_method, ssim_change
from .indices import compute_index
from .postprocessing import morphological_cleanup, remove_small_regions


def compute_metrics(pred_mask: np.ndarray, gt_mask: np.ndarray) -> Dict[str, float]:
    """Compute Precision, Recall, F1-Score, IoU (Jaccard Index), and Overall Accuracy."""
    p = pred_mask > 0
    g = gt_mask > 0

    tp = int(np.sum(p & g))
    fp = int(np.sum(p & (~g)))
    fn = int(np.sum((~p) & g))
    tn = int(np.sum((~p) & (~g)))

    eps = 1e-7
    precision = tp / (tp + fp + eps)
    recall = tp / (tp + fn + eps)
    f1 = 2.0 * precision * recall / (precision + recall + eps)
    iou = tp / (tp + fp + fn + eps)
    total = tp + tn + fp + fn
    accuracy = (tp + tn) / (total + eps)

    return {
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "iou": round(float(iou), 4),
        "accuracy": round(float(accuracy), 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn
    }


def compare_methods(
    before_bands: np.ndarray,
    after_bands: np.ndarray,
    use_case: str,
    is_multispectral: bool = True,
    ground_truth: Optional[np.ndarray] = None,
    threshold_mode: str = "otsu",
    min_area: int = 30
) -> Dict[str, Any]:
    """Execute all applicable DIP change detection methods and compare results.

    Returns metrics table (if ground truth is supplied) and change masks for each method.
    """
    if is_multispectral and before_bands.shape[0] >= 3:
        methods = ["index_differencing", "image_differencing", "pca", "cva", "ssim"]
    else:
        methods = ["image_differencing", "ssim"]

    results: Dict[str, Any] = {}
    metrics_table: List[Dict[str, Any]] = []
    best_f1 = -1.0
    best_method = methods[0]

    for m in methods:
        try:
            raw_res = run_method(
                name=m,
                before_bands=before_bands,
                after_bands=after_bands,
                use_case=use_case,
                is_multispectral=is_multispectral,
                threshold_mode=threshold_mode
            )

            # Standardized postprocessing pipeline
            clean_mask = morphological_cleanup(raw_res["mask"])
            filtered_mask = remove_small_regions(clean_mask, min_area=min_area)

            metrics = None
            if ground_truth is not None:
                metrics = compute_metrics(filtered_mask, ground_truth)
                if metrics["f1_score"] > best_f1:
                    best_f1 = metrics["f1_score"]
                    best_method = m

                metrics_table.append({
                    "method": m,
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1_score": metrics["f1_score"],
                    "iou": metrics["iou"],
                    "accuracy": metrics["accuracy"]
                })

            results[m] = {
                "method": m,
                "diff_map": raw_res["diff_map"],
                "signed_diff": raw_res["signed_diff"],
                "mask": filtered_mask,
                "metrics": metrics
            }
        except Exception as e:
            results[m] = {"error": str(e)}

    return {
        "results": results,
        "metrics_table": metrics_table,
        "best_method": best_method,
        "available_methods": methods
    }


def random_forest_baseline(
    before_bands: np.ndarray,
    after_bands: np.ndarray,
    ground_truth: np.ndarray,
    use_case: str,
    train_ratio: float = 0.25,
    sample_limit: int = 25000
) -> Dict[str, Any]:
    """Train an optional Random Forest pixel classifier as an ML benchmark against DIP methods."""
    c, h, w = before_bands.shape
    features_list = []
    feature_names = []

    # 1. Band difference features (after - before)
    band_diff = after_bands - before_bands
    for b in range(c):
        features_list.append(band_diff[b].ravel())
        feature_names.append(f"band_{b}_diff")

    # 2. Spectral index difference (if multispectral)
    if c >= 3:
        idx1 = compute_index(before_bands, use_case)
        idx2 = compute_index(after_bands, use_case)
        features_list.append((idx2 - idx1).ravel())
        feature_names.append("index_diff")

    # 3. Structural similarity feature
    gray1 = np.mean(before_bands[:3], axis=0) if c >= 3 else before_bands[0]
    gray2 = np.mean(after_bands[:3], axis=0) if c >= 3 else after_bands[0]
    ssim_map, _ = ssim_change(gray1, gray2)
    features_list.append(ssim_map.ravel())
    feature_names.append("ssim_dissimilarity")

    # 4. Local spatial texture gradient
    diff_gray = np.abs(gray2 - gray1)
    laplacian = cv2.Laplacian(diff_gray.astype(np.float32), cv2.CV_32F)
    features_list.append(laplacian.ravel())
    feature_names.append("laplacian_texture")

    # Assemble feature matrix (N, num_features)
    X = np.column_stack(features_list).astype(np.float32)
    y = (ground_truth.ravel() > 0).astype(np.int32)

    # Subsample if pixel count is large for rapid training
    n_samples = X.shape[0]
    indices = np.arange(n_samples)
    if n_samples > sample_limit:
        np.random.seed(42)
        sample_indices = np.random.choice(n_samples, size=sample_limit, replace=False)
        X_sub = X[sample_indices]
        y_sub = y[sample_indices]
    else:
        X_sub = X
        y_sub = y

    X_train, _, y_train, _ = train_test_split(
        X_sub, y_sub, train_size=train_ratio, random_state=42, stratify=y_sub
    )

    clf = RandomForestClassifier(n_estimators=60, max_depth=12, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)

    # Predict change mask on the entire scene
    y_pred = clf.predict(X)
    pred_mask = (y_pred.reshape(h, w) * 255).astype(np.uint8)

    # Postprocessing cleanup
    pred_mask = morphological_cleanup(pred_mask)
    pred_mask = remove_small_regions(pred_mask, min_area=30)

    # Calculate metrics
    metrics = compute_metrics(pred_mask, ground_truth)

    importances = {
        name: round(float(imp), 4)
        for name, imp in zip(feature_names, clf.feature_importances_)
    }

    return {
        "mask": pred_mask,
        "metrics": metrics,
        "feature_importances": importances
    }
