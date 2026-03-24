import sys
import os
from osgeo import gdal
import numpy as np
import cv2


def read_vrt(vrt_path):
    ds = gdal.Open(vrt_path, gdal.GA_ReadOnly)
    if ds is None:
        raise FileNotFoundError(f"The VRT file does not exist.: {vrt_path}")

    band = ds.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    raster = band.ReadAsArray().astype(np.uint8)

    if nodata is not None:
        raster = np.where(raster == nodata, 0, raster)

    transform = ds.GetGeoTransform()
    projection = ds.GetProjection()
    ds = None
    return raster, transform, projection, nodata


def extract_ecological_source(binary_raster, kernel_size=3):
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    core = cv2.erode(binary_raster, kernel, iterations=1)
    return core


def save_as_geotiff(output_path, raster, transform, projection, nodata):
    driver = gdal.GetDriverByName("GTiff")
    creation_options = ["COMPRESS=LZW", "PREDICTOR=2", "TILED=YES", "BIGTIFF=YES"]
    out_raster = driver.Create(
        output_path,
        raster.shape[1],
        raster.shape[0],
        1,
        gdal.GDT_Byte,
        options=creation_options,
    )

    out_raster.SetGeoTransform(transform)
    out_raster.SetProjection(projection)
    out_band = out_raster.GetRasterBand(1)
    out_band.WriteArray(raster)
    if nodata is not None:
        out_band.SetNoDataValue(nodata)
    out_raster.FlushCache()
    out_raster = None
    print(f"Save to: {output_path}")


if __name__ == "__main__":

    y = "2010"
    base_path = r"E:\251120\00_CORE_FORE_GRAS\FOREST"
    vrt_path = os.path.join(base_path, f"CORE_{y}", f"Y{y}.vrt")
    output_path = os.path.join(base_path, f"Core{y}.tif")

    print(f"📂 Read: {vrt_path}")
    print(f"💾 Out : {output_path}")


    binary_raster, transform, projection, nodata_value = read_vrt(vrt_path)

    core_zone = extract_ecological_source(binary_raster, kernel_size=3)


    save_as_geotiff(output_path, core_zone, transform, projection, nodata_value)
