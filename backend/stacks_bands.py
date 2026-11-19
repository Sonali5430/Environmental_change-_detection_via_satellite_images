from pathlib import Path
import rasterio

# Bands you downloaded, in this order
BANDS = ["B02", "B03", "B04", "B08"]

# Project root = the folder above backend
ROOT = Path(__file__).resolve().parent.parent

def stack(folder: Path, out_name: str) -> None:
    tifs = [f for f in folder.glob("*.tif*") if "stack" not in f.name.lower()]
    files = []
    for b in BANDS:
        match = [f for f in tifs if f"_{b}_" in f.name]
        if len(match) != 1:
            raise SystemExit(f"{folder}: expected 1 file for {b}, found {match}")
        files.append(match[0])

    with rasterio.open(files[0]) as ref:
        profile = ref.profile.copy()
        shape = ref.shape
    profile.update(count=len(BANDS), dtype="float32")

    out = folder / out_name
    with rasterio.open(out, "w", **profile) as dst:
        for i, f in enumerate(files, 1):
            with rasterio.open(f) as src:
                if src.shape != shape:
                    raise SystemExit(f"Size mismatch in {f.name}: {src.shape} vs {shape}")
                dst.write(src.read(1).astype("float32"), i)
            dst.set_band_description(i, BANDS[i - 1])
    print("saved", out)

stack(ROOT / "data/raw/water/before", "stack_before.tif")
stack(ROOT / "data/raw/water/after", "stack_after.tif")