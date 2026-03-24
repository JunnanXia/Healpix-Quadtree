from osgeo import gdal
import numpy as np
import cv2
from shapely.geometry import Polygon, MultiPolygon
import time
import sys
from pyproj import CRS
import geopandas as gpd
import pandas as pd
from tqdm import tqdm

def read_vrt_info(vrt_path):
    dataset = gdal.Open(vrt_path)
    geotransform = dataset.GetGeoTransform()
    projection = dataset.GetProjection()
    dataset = None
    return geotransform, projection

def extract_grid_array(dataset, row_min, col_min, row_max, col_max):
    band = dataset.GetRasterBand(1)
    array = band.ReadAsArray(col_min, row_min, col_max - col_min, row_max - row_min)
    band.FlushCache()
    array[array == 0] = 3
    return array

def calculate_bounding_rectangle(x1, y1, x2, y2, x3, y3, x4, y4):
    min_x = min(x1, x2, x3, x4)
    max_x = max(x1, x2, x3, x4)
    min_y = min(y1, y2, y3, y4)
    max_y = max(y1, y2, y3, y4)
    return min_x, min_y, max_x, max_y

def geographic_to_grid(geotransform, min_x, min_y, max_x, max_y):
    inv_geotransform = gdal.InvGeoTransform(geotransform)
    top_left = gdal.ApplyGeoTransform(inv_geotransform, min_x, max_y)
    bottom_right = gdal.ApplyGeoTransform(inv_geotransform, max_x, min_y)
    return map(int, top_left + bottom_right)

def process_diamond_in_vrt(dataset, geotransform, x1, y1, x2, y2, x3, y3, x4, y4):
    min_x, min_y, max_x, max_y = calculate_bounding_rectangle(x1, y1, x2, y2, x3, y3, x4, y4)
    col_min, row_min, col_max, row_max = geographic_to_grid(geotransform, min_x, min_y, max_x, max_y)
    array_content = extract_grid_array(dataset, row_min, col_min, row_max, col_max)
    return array_content

def create_diamond_mask(shape):
    rows, cols = shape
    center_i, center_j = rows // 2, cols // 2
    i, j = np.meshgrid(np.arange(rows), np.arange(cols), indexing='ij')
    mask = np.abs(i - center_i) + np.abs(j - center_j) <= min(center_i, center_j)
    return mask

def max_blob_area(arr, target_value):
    one_hot = np.where(arr == target_value, 1, 0).astype(np.uint8)
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(one_hot, kernel, iterations=2)
    opened = cv2.erode(dilated, kernel, iterations=2)
    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_area = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > max_area:
            max_area = area
    del one_hot, kernel, dilated, opened, contours
    return max_area

def calculate_mode_within_diamond(array, TH=0.75):
    try:
        mask = create_diamond_mask(array.shape[:2])
    except:
        exit()
    diamond_elements = array[mask]
    unique, counts = np.unique(diamond_elements, return_counts=True)
    mode_index = np.argmax(counts)
    mode_value = unique[mode_index]
    mode_count = counts[mode_index]
    total_elements = np.sum(mask)
    mode_ratio = mode_count / total_elements
    del diamond_elements, unique, counts
    if mode_ratio > TH:
        starea = 830
        if total_elements > 3200:
            masked_array = np.where(mask, array, np.nan)
            masked_array = np.where(masked_array == 0, 3, masked_array)
            patch_area1 = max_blob_area(masked_array, 1)
            patch_area2 = max_blob_area(masked_array, 2)
            patch_area3 = max_blob_area(masked_array, 3)
            if mode_value == 3:
                if patch_area1 >= starea or patch_area2 >= starea:
                    splitnot = 1
                else:
                    splitnot = 0
            elif mode_value == 2:
                if patch_area1 >= starea or patch_area3 >= starea:
                    splitnot = 1
                else:
                    splitnot = 0
            else:
                if patch_area2 >= starea or patch_area3 >= starea:
                    splitnot = 1
                else:
                    splitnot = 0
        else:
            splitnot = 0
    else:
        splitnot = 1
    return mode_value, splitnot

def all_process(dataset, geotransform, x1, y1, x2, y2, x3, y3, x4, y4):
    array_content = process_diamond_in_vrt(dataset, geotransform, x1, y1, x2, y2, x3, y3, x4, y4)
    mode_value, splitnot = calculate_mode_within_diamond(array_content)
    del array_content
    return mode_value, splitnot

def ensure_clockwise(A, B, C, D):
    def directed_area(P, Q, R):
        return (Q[0] - P[0]) * (R[1] - P[1]) - (Q[1] - P[1]) * (R[0] - P[0])
    if directed_area(A, B, C) + directed_area(B, C, D) < 0:
        return [A, B, C, D]
    else:
        return [A, D, C, B]

def split_diamond(x1, y1, x2, y2, x3, y3, x4, y4):
    m1_x, m1_y = (x1 + x2) / 2, (y1 + y2) / 2
    m2_x, m2_y = (x2 + x3) / 2, (y2 + y3) / 2
    m3_x, m3_y = (x3 + x4) / 2, (y3 + y4) / 2
    m4_x, m4_y = (x4 + x1) / 2, (y4 + y1) / 2
    center_x, center_y = (x1 + x3) / 2, (y1 + y3) / 2

    diamond1 = ensure_clockwise((x1, y1), (m1_x, m1_y), (center_x, center_y), (m4_x, m4_y))
    diamond2 = ensure_clockwise((m1_x, m1_y), (x2, y2), (m2_x, m2_y), (center_x, center_y))
    diamond3 = ensure_clockwise((center_x, center_y), (m2_x, m2_y), (x3, y3), (m3_x, m3_y))
    diamond4 = ensure_clockwise((m4_x, m4_y), (center_x, center_y), (m3_x, m3_y), (x4, y4))
    return diamond1, diamond2, diamond3, diamond4

def process_diamond(dataset, geotransform, dia, max_level=7):   #Here is where to edit Max Level
    stack = [dia]
    results = []
    while stack:
        x1, y1, x2, y2, x3, y3, x4, y4, level, mode = stack.pop()
        sign = all_process(dataset, geotransform, x1, y1, x2, y2, x3, y3, x4, y4)
        if level >= max_level or sign[1] != 1:
            results.append((x1, y1, x2, y2, x3, y3, x4, y4, level, sign[0]))
        else:
            new_diams = split_diamond(x1, y1, x2, y2, x3, y3, x4, y4)
            new_level = level + 1
            for d in new_diams:
                nx1, ny1 = d[0]
                nx2, ny2 = d[1]
                nx3, ny3 = d[2]
                nx4, ny4 = d[3]
                stack.append((nx1, ny1, nx2, ny2, nx3, ny3, nx4, ny4, new_level, sign[0]))
    return results

def process_polygon(dataset, geotransform, polygon):
    if len(polygon.exterior.coords) < 4:
        return []
    diamond_coords = polygon.exterior.coords[:4]
    x1, y1 = diamond_coords[0]
    x2, y2 = diamond_coords[1]
    x3, y3 = diamond_coords[2]
    x4, y4 = diamond_coords[3]
    diam = (x1, y1, x2, y2, x3, y3, x4, y4, 1, 0)
    return process_diamond(dataset, geotransform, diam)

def process_geometry(dataset, geotransform, geometry):
    all_results = []
    if isinstance(geometry, Polygon):
        all_results.extend(process_polygon(dataset, geotransform, geometry))
    elif isinstance(geometry, MultiPolygon):
        for poly in geometry.geoms:
            all_results.extend(process_polygon(dataset, geotransform, poly))
    return all_results

def save_to_parquet(data, output_path, crs_wkt, batch_size=10000):
    total = len(data)
    total_batches = total // batch_size + (1 if total % batch_size else 0)
    results = []
    pbar = tqdm(total=total_batches, desc="Processing batches")
    for batch_num in range(total_batches):
        batch_data = data[batch_num * batch_size : (batch_num + 1) * batch_size]
        geometries = []
        levels = []
        modes = []
        for x1, y1, x2, y2, x3, y3, x4, y4, level, mode in batch_data:
            poly = Polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)])
            geometries.append(poly)
            levels.append(level)
            modes.append(mode)
        gdf_batch = gpd.GeoDataFrame({
            'geometry': geometries,
            'level': levels,
            'mode': modes
        }, crs=crs_wkt)
        results.append(gdf_batch)
        pbar.update(1)
    pbar.close()
    final_gdf = gpd.GeoDataFrame(pd.concat(results, ignore_index=True), crs=crs_wkt)
    filetype = output_path.split(".")[1]
    if filetype == "parquet":
        final_gdf.to_parquet(output_path)
    else:
        final_gdf.to_file(output_path)
    print(f"Data saved to {output_path}")

if __name__ == '__main__':
    Yearsss = 2020  #Identify the year, any number is ok
    gpkg_path = "testsome.gpkg"   # Input the base grid, Level=1,use proj "+proj=healpix +ellps=WGS84"
    gdf = gpd.read_file(gpkg_path)
    LUCCdata = f"test.tif.0.tif"   #Input the reclassified LUCC map, include urban==1 , agriculture==2 , wildland==3. use proj "+proj=healpix +ellps=WGS84"
    print("Processing" + LUCCdata)
    table_name = f"world{Yearsss}"
    projinfos = read_vrt_info(LUCCdata)

    start_time = time.time()
    geotransform, projection = projinfos

    dataset = gdal.Open(LUCCdata)

    geometries = gdf['geometry'].tolist()
    total_count = len(geometries)

    final_box = []
    for geom in tqdm(geometries, total=total_count, desc="Processing geometries"):
        res = process_geometry(dataset, geotransform, geom)
        final_box.extend(res)

    output_path = f'STT.parquet'  #Output, Where to save the result,Change to parquet can save the hard disk space

    crs_wkt = CRS.from_string("+proj=healpix +ellps=WGS84").to_wkt()

    print(f"Processing and saving to {output_path} ...")
    save_to_parquet(final_box, output_path, crs_wkt)

    print(f"Processing completed. Time taken: {time.time() - start_time:.2f} seconds")
