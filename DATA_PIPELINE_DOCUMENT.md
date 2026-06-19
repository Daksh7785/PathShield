# Data Pipeline Document — Ingestion & Raster Processing

This document explains the Route Resilience data engine, details the multi-resolution satellite data sources, and tracks the tile extraction pipeline.

---

## 1. Supported Data Sources

*   **Cartosat-3 (0.5m Pan, 2.0m MX):** High-resolution indigenous Indian earth observation data. It serves as our challenge dataset for micro-street and junction accuracy evaluation.
*   **Resourcesat LISS-IV (5.8m):** Medium-high resolution multi-spectral bands, ideal for broad suburban network extraction.
*   **Sentinel-2 (10m):** Medium-resolution open-access satellite data. Used for coarse macro-highway routing validations.
*   **OpenStreetMap (OSM):** Serves as ground-truth network vector layers. Automatic rasterizers buffer road LineStrings into binary masks to match tile geometries.
*   **SpaceNet & DeepGlobe:** Pre-training datasets for initial Vision Transformer weight configurations.

---

## 2. Preprocessing & Rasterization Engine

```
 [Raw GeoTIFF Input] ──> [CRS Conversion (WGS84 -> UTM)] ──> [CLAHE Equalization]
                                                                     │
                                                                     ▼
 [OSM Road Vector]   ──> [Buffer & Rasterize]             ──> [Overlapping Tiler]
                                                                     │
                                                                     ▼
                                                             [256x256 Train Patches]
```

### A. Coordinate Reference Systems (CRS) & Projections
To convert from pixel distances to metric lengths, we project lat-long shapes (EPSG:4326) into local Universal Transverse Mercator (UTM) zones (e.g., UTM Zone 43N (EPSG:32643) for Bengaluru). This ensures:
- Metrically accurate road width measurements.
- Exact Euclidean distances for gap-healing heuristics.
- Correct length calculations for graph edge weights.

### B. Tiling & Overlaps
Large sheets are tiled into $256 \times 256$ pixels with a $50\%$ overlap (stride $= 128$). This overlap is crucial:
1.  **Border Integrity:** Roads traversing tile borders are captured in multiple windows, preventing edge clipping.
2.  **Smooth Assembly:** Predictions are reconstructed using a 2D Gaussian kernel blend, eliminating block boundary artifacts.

### C. Occlusion Synthesis (Data Augmentation)
To train the model to "see through" occlusions, we inject synthetic blocks during DataLoader execution:
-   **Building Shadows:** Random dark ellipses tinted using a multiplier ($\alpha \approx 0.65$) and smoothed via Gaussian blur.
-   **Tree Canopy:** Perlin-noise circles colored green and blended to simulate foliage.
-   **Cloud Patches:** White/grey high-frequency noise layers of varying opacity.

---

## 3. Metadata Schema & Tracking
Each tile has an entry in `tiles_metadata.json` mapping its pixel offset to geographical bounds:
```json
{
  "id": 12,
  "filename": "tile_000012.png",
  "pixel_offset": {"x": 128, "y": 0},
  "bounds": {
    "minx": 77.4538,
    "miny": 13.0972,
    "maxx": 77.4612,
    "maxy": 13.1000
  },
  "transform": [0.00003, 0.0, 77.45, 0.0, -0.00003, 13.10]
}
```
This metadata enables mapping skeleton pixel detections back to WGS84 coordinates.
