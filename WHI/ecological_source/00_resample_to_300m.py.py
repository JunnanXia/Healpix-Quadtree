import os
import glob
import gc
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing


input_folder = r"30m_tif_folder"
output_folder = r"300m_tif_folder"
os.makedirs(output_folder, exist_ok=True)


target_crs = "+proj=healpix +ellps=WGS84"
target_res = 300  # meter
valid_classes = {51, 52, 61, 62, 71, 72, 81, 82, 91, 92, 120, 121, 122,130,180}
nodata_val = 0
max_workers = 25

'''
forest
51  Open evergreen broadleaved forest  
52  Closed evergreen broadleaved forest  
61  Open deciduous broadleaved  
62  Closed deciduous broadleaved  
71  Open evergreen needle-leaved  
72  Closed evergreen needle-leaved  
81  Open deciduous needle-leaved  
82  Closed deciduous needle-leaved  
91  Open mixed leaf forest  
92  Closed mixed leaf forest  

Shrubland
120  Shrubland  
121  Evergreen shrubland  
122  Deciduous shrubland  

Wetlands
180  Wetlands

Grassland
130  Grassland


'''


def process_tif(tif_path):
    fname = os.path.basename(tif_path)
    output_path = os.path.join(output_folder, fname.replace(".tif", "_healpix_300m.tif"))

    try:
        with rasterio.open(tif_path) as src:
            # Step 1. 
            arr = src.read(1)
            out_bin = (sum(arr == v for v in valid_classes) > 0).astype("uint8")

            # Step 2. 
            transform, width, height = calculate_default_transform(
                src.crs,
                target_crs,
                src.width,
                src.height,
                *src.bounds,
                resolution=target_res
            )

            profile = src.profile.copy()
            profile.update({
                "crs": target_crs,
                "transform": transform,
                "width": width,
                "height": height,
                "dtype": "uint8",
                "count": 1,
                "compress": "LZW",
                "nodata": nodata_val,
                "driver": "GTiff"
            })

            # Step 3. 
            with rasterio.open(output_path, "w", **profile) as dst:
                reproject(
                    source=out_bin,
                    destination=rasterio.band(dst, 1),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.nearest,
                    src_nodata=None,
                    dst_nodata=nodata_val
                )

        # Step 4. 
        del arr, out_bin
        gc.collect()

        return f"✅ Done: {fname}"

    except Exception as e:
        gc.collect()
        return f"❌ Error processing {fname}: {e}"



if __name__ == "__main__":
    tif_list = sorted(glob.glob(os.path.join(input_folder, "*.tif")))
    print(f"Found {len(tif_list)} TIF files. Using {max_workers} parallel processes...\n")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_tif, tif): tif for tif in tif_list}
        for i, future in enumerate(as_completed(futures), 1):
            print(f"[{i}/{len(futures)}] {future.result()}")

    print("\n🎯 All files processed successfully!")


