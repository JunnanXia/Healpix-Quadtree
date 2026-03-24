# HPQT (HEALPix-Quadtree)

This repository provides a **single-process implementation** of **HPQT (HEALPix-Quadtree)**.

HPQT performs recursive quadtree subdivision of the Earth's surface under the **HEALPix coordinate system**, generating spatial units for spatial identification and analysis.

## Overview

The program takes a Level-1 HEALPix base grid and a classified raster as input, then recursively subdivides each HEALPix diamond according to class dominance and patch structure until the stopping conditions are met or the maximum subdivision level is reached.

The current implementation can support analyses of **three land classes**, for example:

- **1 = urban**
- **2 = agriculture**
- **3 = ecological space**

The output is a vector dataset of adaptively subdivided HEALPix diamond units, with class labels and subdivision levels.

## This repository

This repository contains the **single-process version** of HPQT.

A packaged **multi-process executable** is available at:  
https://zenodo.org/records/19112122

## Coordinate system and raster requirement

This software only supports the following coordinate reference system:

```+proj=healpix +ellps=WGS84```

The current implementation is designed to work properly with raster data in this HEALPix projection at **30 m spatial resolution**.

## Input and output

### Input

The program requires two main inputs:

1. **Base grid**
   - A Level-1 HEALPix vector grid

2. **Classified raster**
   - A raster in `+proj=healpix +ellps=WGS84`
   - Three-class coding, for example:
     - `1` = urban
     - `2` = agriculture
     - `3` = ecological space

### Output

The program outputs a vector dataset containing the subdivided HEALPix units and their attributes, including:

- `geometry`
- `level`
- `mode`

To reduce output size, **Parquet** is used by default.  
The generated Parquet file can be opened and analyzed in **QGIS**.

## Core parameters

The current implementation uses the following key parameters:

- **Maximum subdivision level**: `7`
- **Dominance threshold**: `0.75`
- **Patch-area threshold**: `830`

These parameters control whether a HEALPix unit should continue to be subdivided.

## Included data

This repository includes supporting data for testing and visualization, including:

- an example regional LUCC raster (`.tif`)
- an example grid extent
- an example output file
- a QGIS style file
- a global base HEALPix grid

These files are provided to help users understand the input/output structure and inspect the resulting HPQT units.

## WHI-related materials

The `WHI_paper/` folder contains supplementary materials related to the **WHI (Wildland-Human Interface)** paper, especially the preprocessing workflow for wildland source identification.

These materials are **not part of the HPQT core algorithm**.  
The specific WHI identification workflow can be found in the paper.

## Citation

If you use this repository, please cite the related study:

[...]