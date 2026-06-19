# RouteGuard AI — Data Strategy
## Remote Sensing Data Engine and Preprocessing Pipeline

This document details the data ingestion, validation, and preprocessing pipeline for RouteGuard AI.

---

## 1. Remote Sensing Data Sources

RouteGuard AI ingest both public multispectral datasets and indigenous Indian EO satellite products:

1. **Cartosat-3 (ISRO):** Panchromatic (0.28m) and Multispectral (1.12m) imagery. Serving as the primary source for high-detail metropolitan road layout mapping.
2. **Resourcesat LISS-IV (ISRO):** Multispectral (5.8m) imagery. Ideal for regional connectivity and highway network extraction.
3. **Sentinel-2 (ESA):** Multispectral (10m) bands. Used for broad regional monitoring and cloud-resilient mapping.
4. **SpaceNet (Dataset 3 - Roads):** High-resolution ($30\text{cm}$) satellite imagery with pixel-accurate road centerline geometries. Used as the deep learning training target.
5. **OpenStreetMap (OSM):** Vector road layer downloaded using Overpass API, serving as the ground-truth baseline for rasterization and evaluation.

---

## 2. Ingestion & Preprocessing Pipeline

### Overlapping Sliding Window Tiling
Large satellite scenes ($10000 \times 10000$ pixels) cannot be fed directly to deep learning models due to GPU memory limitations. We implement a sliding window tiling engine:
- **Patch Size:** $256 \times 256$ pixels.
- **Overlap:** 32 pixels (prevents boundary edge prediction artifacts).
- **Stitching:** Gaussian weight blending is used to average predictions at tile boundaries.

### Normalization (CLAHE)
To handle lighting variance (e.g. shadowed streets vs. sunlit rooftops), we apply **Contrast Limited Adaptive Histogram Equalization (CLAHE)**:
- **Clip Limit:** 2.0
- **Grid Size:** $8 \times 8$ pixels
- **Channel Standardizer:** Pixels normalized using ImageNet standard values:
  $$\mu = [0.485, 0.456, 0.406], \quad \sigma = [0.229, 0.224, 0.225]$$

---

## 3. Occlusion Synthesis for Robust Training

To train models to be robust to canopies and shadows, we implement synthetic occlusion generators in the training data loader:

1. **Tree Canopy Simulation:** Random green polygons (opacity 0.7-0.9) drawn along road corridors to simulate tree blocks.
2. **Building Shadow Simulation:** Dark elongated polygons (lowering pixel value by 60%) cast at random angles across intersections.
3. **Cloud Cover Simulation:** Semi-transparent white fractal noise (Perlin noise) overlaying 15% of the tiles.

```python
# Conceptual shadow overlay in dataloader
def apply_shadow(image: np.ndarray, polygon: np.ndarray) -> np.ndarray:
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [polygon], 255)
    shadowed = image.copy()
    shadowed[mask == 255] = (shadowed[mask == 255] * 0.4).astype(np.uint8)
    return shadowed
```
This forces the self-attention mechanism in the Vision Transformer to focus on context lines outside the occluded zone to infer road continuity.
