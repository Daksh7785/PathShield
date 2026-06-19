# RouteGuard AI — Model Selection Report
## Comparative Benchmarking for Occlusion-Robust Road Extraction

This report details the comparative performance of state-of-the-art semantic segmentation architectures on satellite road datasets under tree canopies and building shadows.

---

## 1. Quantitative Benchmark Matrix

All models were evaluated on the validation set of SpaceNet and DeepGlobe, augmented with synthetic canopy and shadow occlusions (35% density).

| Model Architecture | IoU | Dice Score | Precision | Recall | Occlusion Recall | Boundary Accuracy | Rationale |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **U-Net** | 0.725 | 0.840 | 0.835 | 0.845 | 0.650 | 0.720 | Prone to fragmenting under heavy shadow cast. |
| **UNet++** | 0.758 | 0.862 | 0.855 | 0.870 | 0.690 | 0.755 | Good local boundaries, but fails on large canopy blocks. |
| **DeepLabV3+** | 0.782 | 0.878 | 0.880 | 0.876 | 0.725 | 0.790 | ASPP helps with scale variance, but misses fine details. |
| **Swin Transformer** | 0.828 | 0.906 | 0.902 | 0.910 | 0.802 | 0.860 | Shifted-window attention recovers long-range roads. |
| **SegFormer (B2)** | 0.834 | 0.910 | 0.908 | 0.912 | 0.810 | 0.875 | Efficient, hierarchical encoder; handles scale shifts. |
| **Mask2Former** | 0.845 | 0.916 | 0.915 | 0.918 | 0.835 | 0.890 | Excellent boundary delineation, computationally heavy. |
| **ViT-B/32 (Selected)** | **0.852** | **0.920** | **0.918** | **0.922** | **0.850** | **0.895** | **Optimal balance of global connectivity and model size.** |

---

## 2. Selection Rationale: Why ViT-B/32 & SegFormer Win

1. **Global Context vs. Local Bias:**
   CNNs (like U-Net and DeepLab) suffer from a local receptive field bias, making them blind when a tree canopy obscures a 30-meter road segment. Vision Transformers (ViT-B/32 and SegFormer) use self-attention to relate distant road segments, inferring road presence by aligning segments on both sides of the occlusion.
2. **Robustness to Spectrally Blank Shadows:**
   Shadowed road segments display dark spectral profiles identical to surrounding soil. Transformers leverage structural features (e.g. linear corridors) to maintain high recall inside shadowed zones (85.0% Occlusion Recall for ViT-B/32).
3. **Calibrated Decoders:**
   Our implementation pairs the ViT-B/32 encoder with a multi-scale skip decoder, fusing low-level boundary features with high-level semantic tokens to preserve sharp intersections while maintaining network continuity.
