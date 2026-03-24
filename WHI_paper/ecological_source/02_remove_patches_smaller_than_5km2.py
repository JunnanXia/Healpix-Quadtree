import rasterio
import numpy as np
from scipy.ndimage import label
import psutil
import gc
import time




def main():
    years = [2000, 2005, 2010, 2015, 2020]
    types = ["FOREST", "GRASS"]

    for y in years:
        for x in types:


            input_tif = rf"Core_{str(y)}.tif"
            output_tif = rf"Core_{str(y)}_5km2.tif"

            pixel_size = 300  # （m）
            min_area_km2 = 5  #  (km²)
            ROI_mean = 0.849  # 
            connectivity = 4  # 
            compress_method = "lzw"  # 

            t0 = time.time()
            print("Reading...")
            with rasterio.open(input_tif) as src:
                data = src.read(1)
                nodata = src.nodata
                profile = src.profile

            print(f"Data Size: {data.shape}, dtype={data.dtype}")
            print(f"System Available Memory: {psutil.virtual_memory().available/1e9:.1f} GB")


            if nodata is not None:
                data = np.where(data == nodata, 0, data)
            data = (data == 1).astype(np.uint8)


            min_pixels_geom = (min_area_km2 * 1e6) / (pixel_size ** 2)
            min_pixels_ellipsoid = int(np.ceil(min_pixels_geom / ROI_mean))
            print(f"Area Threshold: {min_area_km2} km² ≈ {min_pixels_ellipsoid} Pixel (Corrected)")


            print("Performing connected component analysis......")
            structure = np.array([[0,1,0],[1,1,1],[0,1,0]], dtype=int) if connectivity == 4 else np.ones((3,3), int)
            labeled, num = label(data, structure=structure)
            print(f"Number of Connected Patches Detected: {num:,}")


            sizes = np.bincount(labeled.ravel())
            keep = sizes >= min_pixels_ellipsoid
            keep[0] = False
            filtered = keep[labeled]

            del data, labeled, sizes, keep
            gc.collect()

            print("Saving...")
            profile.update(dtype=rasterio.uint8, compress=compress_method, nodata=0)
            with rasterio.open(output_tif, "w", **profile) as dst:
                dst.write(filtered.astype(np.uint8), 1)

            elapsed = time.time() - t0
            print(f"Processing complete, results saved to: {output_tif}")
            print(f"Time: {elapsed/60:.2f} m")

if __name__ == "__main__":
    main()
