# Wildland source workflow

This folder contains several auxiliary scripts used to derive **wildland sources** for the WHI study.

These scripts are not part of the HPQT core algorithm.  
They are provided only as supporting preprocessing materials for the broader WHI workflow.

## Main steps

1. Reclassify land-cover data and reproject to the **HEALPix CRS**
2. Resample to **300 m**
3. Extract core wildland areas
4. Remove patches smaller than **5 km²**
5. Expand retained wildland sources

## Note

The main focus of this repository is the **HPQT (HEALPix-based Quadtree)** algorithm.  
This folder only contains a supplementary workflow used in the WHI study.