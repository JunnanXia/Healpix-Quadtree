# HPQT Single-Process Reference Implementation

This repository provides a **single-process reference implementation** of the **HPQT (HEALPix-based Quadtree)** algorithm.

## What this repository is

This code is **not the WHI algorithm itself**.  
Instead, it implements the **HPQT spatial subdivision procedure** that is used to support WHI mapping and delineation workflows.

In our workflow, HPQT is used as the adaptive spatial partitioning framework on a HEALPix-based diamond grid. It recursively subdivides each Level-1 base unit into smaller diamond cells according to class dominance and patch-structure criteria derived from a reclassified land-use / land-cover raster.

## Relationship to WHI

- **HPQT**: the recursive spatial subdivision algorithm implemented here
- **WHI**: the downstream wildland–human interface mapping framework supported by HPQT outputs

This repository is intended to provide a **transparent, reproducible, single-process baseline implementation** of HPQT for methodological inspection and academic reproducibility.

## Multi-process version

A **multi-process executable release** is available separately at Zenodo:

**https://zenodo.org/records/19112122**

The multi-process version is intended for production-scale execution and substantially faster processing of large datasets.

## Core idea

For each HEALPix diamond unit, the algorithm:

1. Reads the corresponding raster window from the reclassified LUCC dataset.
2. Applies a diamond-shaped mask within the bounding raster window.
3. Computes the dominant class within the diamond.
4. Evaluates whether the unit should be subdivided further using:
   - a dominance threshold, and
   - patch-area conditions based on connected blob size.
5. Recursively splits the diamond into four sub-diamonds until:
   - the stopping rule is met, or
   - the maximum recursion level is reached.

## Input requirements

### 1. Base grid
A Level-1 HEALPix diamond grid stored as a vector file, for example:

- `testsome.gpkg`

The geometry is expected to use a HEALPix CRS such as:

```text
+proj=healpix +ellps=WGS84