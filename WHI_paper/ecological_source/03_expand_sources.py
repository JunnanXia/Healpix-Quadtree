
import rasterio
from rasterio.enums import Resampling
from scipy.ndimage import binary_dilation
import numpy as np
import os



def expand_binary_raster(input_tif, output_tif, expand_pixels, nodata_val=0):
    print(f"Reading: {os.path.basename(input_tif)}")
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        profile = src.profile

    # 将 nodata 替换为 0
    data = np.where(data == nodata_val, 0, data)
    binary = (data == 1)

    print(f"expand {expand_pixels}expand_pixels...")
    structure = np.ones((3, 3), dtype=bool)
    expanded = binary_dilation(binary, structure=structure, iterations=expand_pixels)

    out = np.where(expanded, 1, 0).astype(np.uint8)

    profile.update(dtype=rasterio.uint8, compress="lzw", nodata=nodata_val)

    with rasterio.open(output_tif, "w", **profile) as dst:
        dst.write(out, 1)

    print(f"Save to: {output_tif}")

if __name__ == "__main__":
    # ================= 用户参数 =================
    input_tif = rf"Core_2020__5km2.tif"
    output_tif = rf"Core_2020__5km2_buffer8.tif"

    expand_pixels = 8  # 向外扩展像元数
    nodata_val = 0  # 背景值
    # ===========================================
    expand_binary_raster(input_tif, output_tif, expand_pixels, nodata_val)