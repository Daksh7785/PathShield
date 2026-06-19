# RouteGuard AI — Literature Review
## State-of-the-Art in Remote Sensing, Graph Theory, and Urban Resilience

This document reviews the scientific literature underpinning RouteGuard AI, detailing deep learning semantic segmenters, centerline thinners, topological healing, and graph-theoretic vulnerability simulations.

---

## 1. Remote Sensing & Road Extraction Datasets

1. **SpaceNet (Roads and Buildings Dataset):**
   - *Key Insight:* Features sub-meter resolution imagery (DigitalGlobe) paired with detailed road centerlines. Emphasizes that traditional pixel-based IoU is insufficient for routing; instead, they introduce the **Average Path Length Similarity (APLS)** metric to evaluate topological correctness.
2. **DeepGlobe Road Extraction Challenge:**
   - *Key Insight:* Consists of RGB satellite images ($1024 \times 1024$) capturing diverse rural and urban environments. Shows that standard CNNs fail in forested regions where vegetation canopies shade roads.
3. **OpenSatMap & OpenStreetMap (OSM) Rasterizer:**
   - *Key Insight:* Emphasizes using OpenStreetMap road geometries to automatically generate binary segmentation masks, demonstrating how online vector repositories can serve as dense training targets.

---

## 2. Segmentation & Road Inpainting Architectures

1. **SegFormer: Simple and Efficient Design with Transformers (Xie et al., 2021):**
   - *Key Insight:* Uses a hierarchical Transformer encoder that outputs multi-scale features without positional encodings, yielding robust road predictions even when local features are occluded.
2. **Mask2Former for Universal Image Segmentation (Cheng et al., 2022):**
   - *Key Insight:* Introduces masked attention to focus on localized road regions, improving boundary accuracy and reducing false-positive road classifications.
3. **DeepLabV3+: Encoder-Decoder with Atrous Separable Convolution (Chen et al., 2018):**
   - *Key Insight:* Employs spatial pyramid pooling (ASPP) to capture multi-scale context, serving as a strong baseline for mapping urban highways.
4. **RoadFormer: Du et al. (2023):**
   - *Key Insight:* Combines CNNs for local texture capture with Vision Transformers for long-range connectivity reasoning, maintaining road continuity under tree canopies.

---

## 3. Network Science & Centrality Algorithms

1. **Brandes' Algorithm for Betweenness Centrality (Brandes, 2001):**
   - *Key Insight:* Computes betweenness centrality in $O(V \cdot E)$ time for unweighted graphs and $O(V \cdot E + V^2 \log V)$ for weighted graphs. This is the mathematical backbone for detecting gatekeeper intersections.
2. **Urban Network Robustness (Albert & Barabási, 2002):**
   - *Key Insight:* Shows that scale-free urban networks are highly robust to random failures but extremely vulnerable to targeted attacks on high-degree or high-centrality hubs.
3. **Topological Healing and Bridge Recovery:**
   - *Key Insight:* Reconstructs fragmented lines using Minimum Spanning Trees (MST) and Delaunay Triangulation, showing that angular constraints prevent false-positive links between parallel streets.
