import glob, os
import rasterio

BANDS = ["B03", "B04", "B08", "B11", "B12"]

def stack(folder, out_name):
    tifs = [f for f in glob.glob(os.path.join(folder, "*.tif*"))
            if "STACK" not in os.path.basename(f).upper()]
    files = []
    for b in BANDS:
        match = [f for f in tifs if b in os.path.basename(f).upper()]
        if len(match) != 1:
            raise SystemExit(f"{folder}: expected 1 file for {b}, found {match}")
        files.append(match[0])

    with rasterio.open(files[0]) as ref:
        profile = ref.profile.copy()
    profile.update(count=len(BANDS), dtype="float32")

    out = os.path.join(folder, out_name)
    with rasterio.open(out, "w", **profile) as dst:
        for i, f in enumerate(files, 1):
            with rasterio.open(f) as src:
                dst.write(src.read(1).astype("float32"), i)
            dst.set_band_description(i, BANDS[i - 1])
    print("saved", out)

stack("../data/raw/water/before", "stack_before.tif")
stack("../data/raw/water/after", "stack_after.tif")