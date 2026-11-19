"""Router for initiating and polling change detection analyses."""

import json
import shutil
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..database import get_db, SessionLocal
from ..models import Analysis
from ..schemas import AnalysisStatusResponse
from ..services.change_detection import run_method
from ..services.evaluation import compute_metrics
from ..services.indices import USE_CASES
from ..services.postprocessing import (
    compute_statistics,
    make_overlay,
    mask_to_geojson,
    morphological_cleanup,
    remove_small_regions,
)
from ..services.preprocessing import preprocess_pair
from ..services.registration import align_pair
from ..services.utils import load_image, pixel_area_m2, save_png

router = APIRouter(prefix="/analyze", tags=["Analyze"])

# Directory configuration
backend_dir = Path(__file__).resolve().parents[2]
uploads_base = backend_dir / "storage" / "uploads"
outputs_base = backend_dir / "storage" / "outputs"


def hex_to_rgb(hex_code: str) -> tuple[int, int, int]:
    """Convert hex string (e.g. '#22c55e') to RGB tuple."""
    hex_clean = hex_code.lstrip("#")
    if len(hex_clean) == 6:
        return tuple(int(hex_clean[i:i + 2], 16) for i in (0, 2, 4))
    return (239, 68, 68)


def run_analysis_pipeline(
    analysis_id: str,
    before_path: str,
    after_path: str,
    gt_path: Optional[str],
    use_case: str,
    method: str,
    min_area: int,
    threshold_mode: str,
    threshold_val: Optional[float]
):
    """Background task executing the complete DIP change detection pipeline."""
    db = SessionLocal()
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        db.close()
        return

    try:
        analysis.status = "running"
        db.commit()

        out_dir = outputs_base / analysis_id
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Load images & inspect metadata
        before_info = load_image(before_path)
        after_info = load_image(after_path)

        is_multi = before_info["is_multispectral"] and after_info["is_multispectral"]
        analysis.is_multispectral = is_multi

        # Validation: spectral indices cannot run on plain RGB images
        if not is_multi and method.lower().strip() in ("index_differencing", "index"):
            raise ValueError(
                "RGB images detected: spectral indices (NDVI/NDWI/NBR/NDBI) are unavailable. "
                "Please select Image Differencing, PCA, or SSIM for RGB imagery."
            )

        # 2. Co-registration and spatial alignment
        aligned_after, reg_log = align_pair(before_info, after_info)

        # 3. Radiometric normalization, cloud masking, and denoising
        clean_before, clean_after, valid_mask = preprocess_pair(
            before_info["bands"],
            aligned_after,
            do_denoise=True,
            do_match=True
        )

        # 4. DIP Change Detection Algorithm
        cd_res = run_method(
            name=method,
            before_bands=clean_before,
            after_bands=clean_after,
            use_case=use_case,
            is_multispectral=is_multi,
            threshold_mode=threshold_mode,
            threshold_val=threshold_val
        )

        # 5. Morphological postprocessing and small component filtering
        cleaned_mask = morphological_cleanup(cd_res["mask"], ksize=5)
        final_mask = remove_small_regions(cleaned_mask, min_area=min_area)

        # Mask invalid/cloud pixels only if valid_mask is reasonable
        if valid_mask is not None and valid_mask.sum() > 0.1 * valid_mask.size:
            final_mask = final_mask * valid_mask.astype(final_mask.dtype)

        # 6. Quantitative Statistics Calculation
        px_area = pixel_area_m2(before_info.get("transform"), before_info.get("crs"))
        stats = compute_statistics(
            mask=final_mask,
            signed_diff=cd_res["signed_diff"],
            pixel_area_m2=px_area,
            use_case=use_case
        )

        # 7. Ground Truth Evaluation Metrics (if GT file provided)
        metrics = None
        if gt_path and Path(gt_path).exists():
            gt_info = load_image(gt_path)
            gt_arr = gt_info["bands"][0] > 0
            metrics = compute_metrics(final_mask, gt_arr)

        # 8. Render and save visual output artifacts
        save_png(clean_before, str(out_dir / "before_preview.png"))
        save_png(clean_after, str(out_dir / "after_preview.png"))
        save_png(cd_res["diff_map"], str(out_dir / "diff.png"))
        save_png(final_mask, str(out_dir / "change_mask.png"))

        # Visual change overlay with use case theme accent color
        color_hex = USE_CASES.get(use_case, {}).get("accent_color", "#ef4444")
        accent_rgb = hex_to_rgb(color_hex)
        overlay = make_overlay(clean_after, final_mask, color=accent_rgb, alpha=0.45)
        save_png(overlay, str(out_dir / "overlay.png"))

        # Vector GeoJSON export
        geojson_data = mask_to_geojson(
            final_mask,
            transform=before_info.get("transform"),
            crs=before_info.get("crs")
        )
        with open(out_dir / "change.geojson", "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, indent=2)

        # Save JSON payload into database
        summary_payload = {
            "stats": stats,
            "metrics": metrics,
            "registration_log": reg_log,
            "is_multispectral": is_multi
        }
        analysis.stats_json = json.dumps(summary_payload)
        analysis.status = "done"
        analysis.error = None
        db.commit()

    except Exception as e:
        analysis.status = "failed"
        analysis.error = str(e)
        db.commit()
    finally:
        db.close()


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def analyze_images(
    background_tasks: BackgroundTasks,
    before: UploadFile = File(..., description="Before satellite image (GeoTIFF or RGB)"),
    after: UploadFile = File(..., description="After satellite image (GeoTIFF or RGB)"),
    use_case: str = Form("deforestation", description="Environmental use case"),
    method: str = Form("index_differencing", description="DIP Change detection method"),
    ground_truth: Optional[UploadFile] = File(None, description="Optional ground truth change mask"),
    min_area: int = Form(30, description="Minimum region pixel threshold"),
    threshold_mode: str = Form("otsu", description="Thresholding mode: otsu, adaptive, manual"),
    threshold_val: Optional[float] = Form(None, description="Manual threshold cutoff (0.0 to 1.0)"),
    db: Session = Depends(get_db)
):
    """Upload image pair and initiate asynchronous change detection pipeline."""
    uc_clean = use_case.lower().strip()
    if uc_clean not in USE_CASES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid use case '{use_case}'. Supported options: {list(USE_CASES.keys())}"
        )

    analysis_id = uuid.uuid4().hex[:12]
    upload_dir = uploads_base / analysis_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    output_dir = outputs_base / analysis_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded files to disk
    before_save_path = upload_dir / before.filename
    with open(before_save_path, "wb") as buffer:
        shutil.copyfileobj(before.file, buffer)

    after_save_path = upload_dir / after.filename
    with open(after_save_path, "wb") as buffer:
        shutil.copyfileobj(after.file, buffer)

    gt_save_path = None
    if ground_truth and ground_truth.filename:
        gt_save_path = upload_dir / ground_truth.filename
        with open(gt_save_path, "wb") as buffer:
            shutil.copyfileobj(ground_truth.file, buffer)

    # Insert preliminary record in SQLite
    new_analysis = Analysis(
        id=analysis_id,
        use_case=uc_clean,
        method=method.lower().strip(),
        status="pending",
        before_name=before.filename,
        after_name=after.filename,
        is_multispectral=True,
        output_dir=str(output_dir),
        stats_json=None,
        error=None
    )
    db.add(new_analysis)
    db.commit()
    db.refresh(new_analysis)

    # Enqueue background image processing task
    background_tasks.add_task(
        run_analysis_pipeline,
        analysis_id=analysis_id,
        before_path=str(before_save_path),
        after_path=str(after_save_path),
        gt_path=str(gt_save_path) if gt_save_path else None,
        use_case=uc_clean,
        method=method.lower().strip(),
        min_area=min_area,
        threshold_mode=threshold_mode.lower().strip(),
        threshold_val=threshold_val
    )

    return {
        "id": analysis_id,
        "status": "pending",
        "message": "Change detection analysis queued successfully."
    }


@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
def get_analysis_status(analysis_id: str, db: Session = Depends(get_db)):
    """Poll execution status of an ongoing analysis."""
    item = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID '{analysis_id}' not found."
        )
    return item

