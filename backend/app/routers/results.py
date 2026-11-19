"""Router for retrieving analysis results, multi-method comparison, history, and use cases."""

import json
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Analysis
from ..schemas import (
    AnalysisResultResponse,
    AnalysisUrls,
    CompareResultResponse,
    HistoryItem,
    UseCaseInfo,
)
from ..services.evaluation import compare_methods
from ..services.indices import USE_CASES
from ..services.preprocessing import preprocess_pair
from ..services.registration import align_pair
from ..services.utils import load_image, save_png

router = APIRouter(tags=["Results"])

# Directory configuration
backend_dir = Path(__file__).resolve().parents[2]
uploads_base = backend_dir / "storage" / "uploads"
outputs_base = backend_dir / "storage" / "outputs"


@router.get("/results/{analysis_id}", response_model=AnalysisResultResponse)
def get_analysis_results(analysis_id: str, db: Session = Depends(get_db)):
    """Retrieve full statistical report and visual asset links for an analysis."""
    item = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis '{analysis_id}' not found."
        )

    if item.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Analysis failed: {item.error}"
        )

    stats = None
    metrics = None
    if item.stats_json:
        try:
            payload = json.loads(item.stats_json)
            stats = payload.get("stats")
            metrics = payload.get("metrics")
        except Exception:
            pass

    # Static asset URLs mounted under /outputs/
    urls = AnalysisUrls(
        before_preview=f"/outputs/{analysis_id}/before_preview.png",
        after_preview=f"/outputs/{analysis_id}/after_preview.png",
        diff=f"/outputs/{analysis_id}/diff.png",
        change_mask=f"/outputs/{analysis_id}/change_mask.png",
        overlay=f"/outputs/{analysis_id}/overlay.png",
        geojson=f"/outputs/{analysis_id}/change.geojson"
    )

    return AnalysisResultResponse(
        id=item.id,
        status=item.status,
        created_at=item.created_at,
        use_case=item.use_case,
        method=item.method,
        is_multispectral=item.is_multispectral,
        stats=stats,
        metrics=metrics,
        urls=urls,
        error=item.error
    )


@router.get("/compare/{analysis_id}", response_model=CompareResultResponse)
def get_method_comparison(analysis_id: str, db: Session = Depends(get_db)):
    """Run all applicable DIP methods across the uploaded image pair and return metrics benchmark."""
    item = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis '{analysis_id}' not found."
        )

    upload_dir = uploads_base / analysis_id
    before_path = upload_dir / item.before_name
    after_path = upload_dir / item.after_name

    if not before_path.exists() or not after_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source image files not found on disk."
        )

    # 1. Load and align
    before_info = load_image(str(before_path))
    after_info = load_image(str(after_path))
    aligned_after, _ = align_pair(before_info, after_info)

    # 2. Preprocess
    clean_before, clean_after, _ = preprocess_pair(
        before_info["bands"], aligned_after, do_denoise=True, do_match=True
    )

    # 3. Check for ground truth
    gt_arr = None
    for file in upload_dir.iterdir():
        if "ground_truth" in file.name.lower() or "gt" in file.name.lower():
            try:
                gt_data = load_image(str(file))
                gt_arr = (gt_data["bands"][0] > 0).astype(int)
                break
            except Exception:
                pass

    is_multi = before_info["is_multispectral"] and after_info["is_multispectral"]

    # 4. Run DIP multi-method comparison
    comp_results = compare_methods(
        before_bands=clean_before,
        after_bands=clean_after,
        use_case=item.use_case,
        is_multispectral=is_multi,
        ground_truth=gt_arr,
        threshold_mode="otsu",
        min_area=30
    )

    # 5. Save per-method preview masks to outputs/<id>/methods/
    methods_dir = outputs_base / analysis_id / "methods"
    methods_dir.mkdir(parents=True, exist_ok=True)

    mask_urls = {}
    for m_name, m_data in comp_results["results"].items():
        if "mask" in m_data:
            mask_filename = f"mask_{m_name}.png"
            save_png(m_data["mask"], str(methods_dir / mask_filename))
            mask_urls[m_name] = f"/outputs/{analysis_id}/methods/{mask_filename}"

    return CompareResultResponse(
        id=item.id,
        use_case=item.use_case,
        best_method=comp_results["best_method"],
        metrics_table=comp_results["metrics_table"],
        method_mask_urls=mask_urls,
        is_multispectral=is_multi
    )


@router.get("/history", response_model=List[HistoryItem])
def get_analysis_history(db: Session = Depends(get_db)):
    """Retrieve chronologically ordered log of past analyses."""
    items = db.query(Analysis).order_by(Analysis.created_at.desc()).all()
    history = []

    for item in items:
        pct_change = None
        chg_km2 = None
        if item.stats_json:
            try:
                payload = json.loads(item.stats_json)
                st = payload.get("stats", {})
                pct_change = st.get("percent_change")
                chg_km2 = st.get("changed_km2")
            except Exception:
                pass

        overlay_url = f"/outputs/{item.id}/overlay.png" if item.status == "done" else None
        thumb_url = f"/outputs/{item.id}/after_preview.png" if item.status == "done" else None

        history.append(
            HistoryItem(
                id=item.id,
                created_at=item.created_at,
                use_case=item.use_case,
                method=item.method,
                status=item.status,
                before_name=item.before_name,
                after_name=item.after_name,
                percent_change=pct_change,
                changed_km2=chg_km2,
                overlay_url=overlay_url,
                thumbnail_url=thumb_url
            )
        )
    return history


@router.get("/usecases", response_model=List[UseCaseInfo])
def get_use_cases():
    """Retrieve catalog of supported environmental monitoring applications and spectral configs."""
    return [UseCaseInfo(**uc) for uc in USE_CASES.values()]


@router.delete("/history/{analysis_id}")
def delete_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Purge an analysis record and delete stored artifact assets."""
    item = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis '{analysis_id}' not found."
        )

    # Clean storage folders
    upload_dir = uploads_base / analysis_id
    output_dir = outputs_base / analysis_id
    if upload_dir.exists():
        shutil.rmtree(upload_dir, ignore_errors=True)
    if output_dir.exists():
        shutil.rmtree(output_dir, ignore_errors=True)

    db.delete(item)
    db.commit()

    return {"message": f"Analysis '{analysis_id}' and associated files deleted successfully."}
