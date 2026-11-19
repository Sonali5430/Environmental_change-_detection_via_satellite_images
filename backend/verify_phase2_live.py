"""Live Phase 2 Verification Script.

Starts real Uvicorn server in a background thread and calls all REST endpoints
using requests on synthetic multi-spectral satellite data.
"""

import os
import sys
import time
import threading
from pathlib import Path
import requests

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

import uvicorn
from app.main import app
from app.services.utils import generate_synthetic_pair

SERVER_PORT = 8000
BASE_URL = f"http://127.0.0.1:{SERVER_PORT}/api"


def start_server():
    config = uvicorn.Config(app=app, host="127.0.0.1", port=SERVER_PORT, log_level="error")
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None
    server.run()


def run_verification():
    print("=" * 60)
    print("PHASE 2 VERIFICATION: FastAPI + Uvicorn Live Server Testing")
    print("=" * 60)

    # 1. Start Uvicorn in background daemon thread
    print("\n[Step 1] Starting Uvicorn server on http://127.0.0.1:8000...")
    t = threading.Thread(target=start_server, daemon=True)
    t.start()

    # Wait for server to bind and respond
    max_retries = 30
    server_ready = False
    for i in range(max_retries):
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=1)
            if r.status_code == 200:
                server_ready = True
                print(f"  [OK] Server is live! Health check: {r.json()}")
                break
        except Exception:
            time.sleep(0.5)

    if not server_ready:
        print("  [ERROR] Server failed to start within timeout.")
        sys.exit(1)

    # 2. Test use cases catalog
    print("\n[Step 2] Testing GET /api/usecases...")
    r = requests.get(f"{BASE_URL}/usecases", timeout=5)
    assert r.status_code == 200, f"Error: {r.text}"
    usecases = r.json()
    print(f"  [OK] Retrieved {len(usecases)} use cases:")
    for uc in usecases:
        print(f"    - {uc['name']} (Index: {uc['index_name']}, Accent: {uc['accent_color']})")

    # 3. Prepare synthetic data
    print("\n[Step 3] Preparing synthetic data pair for Deforestation...")
    project_root = backend_dir.parent
    paths = generate_synthetic_pair("deforestation", size=256, base_dir=str(project_root))
    before_p = Path(paths["before_path"])
    after_p = Path(paths["after_path"])
    gt_p = Path(paths["ground_truth_path"])
    print(f"  [OK] Synthetic files ready at: {before_p.parent.name}")

    # 4. POST /api/analyze
    print("\n[Step 4] Testing POST /api/analyze (uploading image pair)...")
    with open(before_p, "rb") as fb, open(after_p, "rb") as fa, open(gt_p, "rb") as fgt:
        files = {
            "before": (before_p.name, fb, "image/tiff"),
            "after": (after_p.name, fa, "image/tiff"),
            "ground_truth": (gt_p.name, fgt, "image/png")
        }
        data = {
            "use_case": "deforestation",
            "method": "index_differencing",
            "min_area": "25",
            "threshold_mode": "otsu"
        }
        r = requests.post(f"{BASE_URL}/analyze", files=files, data=data, timeout=10)

    assert r.status_code == 202, f"Expected 202, got {r.status_code}: {r.text}"
    analysis_id = r.json()["id"]
    print(f"  [OK] Analysis queued with ID: {analysis_id}")

    # 5. Poll status GET /api/analyze/{id}/status
    print("\n[Step 5] Polling GET /api/analyze/{id}/status...")
    done = False
    for i in range(30):
        r = requests.get(f"{BASE_URL}/analyze/{analysis_id}/status", timeout=5)
        assert r.status_code == 200, f"Error: {r.text}"
        st = r.json()["status"]
        print(f"  Poll {i+1}: status = {st}")
        if st == "done":
            done = True
            break
        elif st == "failed":
            raise RuntimeError(f"Analysis failed: {r.json().get('error')}")
        time.sleep(1)

    assert done, "Analysis did not finish in time"
    print("  [OK] Background processing task completed successfully!")

    # 6. Retrieve results GET /api/results/{id}
    print(f"\n[Step 6] Testing GET /api/results/{analysis_id}...")
    r = requests.get(f"{BASE_URL}/results/{analysis_id}", timeout=5)
    assert r.status_code == 200, f"Error: {r.text}"
    res = r.json()
    print("  Quantitative Statistics:")
    for k, v in res["stats"].items():
        print(f"    - {k}: {v}")
    if res.get("metrics"):
        print("  Ground Truth Evaluation Metrics:")
        for k, v in res["metrics"].items():
            if isinstance(v, float):
                print(f"    - {k}: {v:.4f}")
    print("  Output Asset URLs:")
    for k, v in res["urls"].items():
        print(f"    - {k}: {v}")

    # 7. Static file verification
    print("\n[Step 7] Testing static file serving from /outputs...")
    overlay_url = f"http://127.0.0.1:{SERVER_PORT}{res['urls']['overlay']}"
    geojson_url = f"http://127.0.0.1:{SERVER_PORT}{res['urls']['geojson']}"
    r_over = requests.get(overlay_url, timeout=5)
    assert r_over.status_code == 200, "Overlay static file failed"
    r_geo = requests.get(geojson_url, timeout=5)
    assert r_geo.status_code == 200, "GeoJSON static file failed"
    print(f"  [OK] Static overlay.png ({len(r_over.content)} bytes) and change.geojson ({len(r_geo.content)} bytes) served correctly.")

    # 8. Compare methods GET /api/compare/{id}
    print(f"\n[Step 8] Testing GET /api/compare/{analysis_id}...")
    r = requests.get(f"{BASE_URL}/compare/{analysis_id}", timeout=15)
    assert r.status_code == 200, f"Error: {r.text}"
    comp = r.json()
    print(f"  Best Method: {comp['best_method']}")
    print("-" * 75)
    print(f"{'Method':<22} | {'Precision':<9} | {'Recall':<9} | {'F1-Score':<9} | {'IoU':<9} | {'Accuracy':<9}")
    print("-" * 75)
    for row in comp["metrics_table"]:
        print(f"{row['method']:<22} | {row['precision']:<9.4f} | {row['recall']:<9.4f} | {row['f1_score']:<9.4f} | {row['iou']:<9.4f} | {row['accuracy']:<9.4f}")
    print("-" * 75)

    # 9. History GET /api/history
    print("\n[Step 9] Testing GET /api/history...")
    r = requests.get(f"{BASE_URL}/history", timeout=5)
    assert r.status_code == 200, f"Error: {r.text}"
    history = r.json()
    print(f"  [OK] History records count: {len(history)}")
    assert any(h["id"] == analysis_id for h in history)

    print("\n" + "=" * 60)
    print("ALL PHASE 2 FASTAPI & UVICORN ENDPOINTS VERIFIED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_verification()
