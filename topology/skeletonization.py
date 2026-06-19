"""
Convert binary road mask → 1-pixel-wide skeleton → junction/endpoint graph nodes.
Uses Zhang-Suen thinning algorithm via scikit-image.
"""
import cv2
import numpy as np
from skimage.morphology import skeletonize, remove_small_objects
from skimage.measure import label
from typing import Tuple
import json


def clean_binary_mask(
    mask: np.ndarray,
    min_area_px: int = 50,
    morph_open_size: int = 3,
    morph_close_size: int = 5,
) -> np.ndarray:
    """
    Clean binary road mask before skeletonization.
    Removes noise, fills small gaps, removes tiny disconnected components.
    """
    binary = (mask > 127).astype(bool)
    
    # Morphological opening: remove small noise
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_open_size, morph_open_size))
    cleaned = cv2.morphologyEx(binary.astype(np.uint8) * 255, cv2.MORPH_OPEN, kernel_open)
    
    # Morphological closing: fill small gaps in roads
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_close_size, morph_close_size))
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel_close)
    
    # Remove small disconnected components
    binary_cleaned = (cleaned > 127).astype(bool)
    binary_cleaned = remove_small_objects(binary_cleaned, min_size=min_area_px)
    
    return binary_cleaned.astype(np.uint8) * 255


def skeletonize_mask(mask: np.ndarray) -> np.ndarray:
    """
    Apply Zhang-Suen thinning to get 1-pixel-wide road centerlines.
    Returns binary array (H, W) with 1=road centerline, 0=background.
    """
    binary = (mask > 127).astype(bool)
    skeleton = skeletonize(binary, method='zhang')
    return skeleton.astype(np.uint8)


def get_neighbor_count(skeleton: np.ndarray, y: int, x: int) -> int:
    """Count 8-connected neighbors for a skeleton pixel."""
    H, W = skeleton.shape
    count = 0
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dy == 0 and dx == 0:
                continue
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and skeleton[ny, nx]:
                count += 1
    return count


def extract_graph_nodes(skeleton: np.ndarray) -> dict:
    """
    Extract junction points (degree > 2) and endpoints (degree == 1) from skeleton.
    
    Returns:
        {
          'junctions': [(y, x), ...],    # intersections
          'endpoints': [(y, x), ...],    # dead ends
          'isolated': [(y, x), ...]      # isolated pixels (degree 0 with road)
        }
    """
    nodes = {'junctions': [], 'endpoints': [], 'isolated': []}
    ys, xs = np.where(skeleton > 0)
    
    for y, x in zip(ys, xs):
        deg = get_neighbor_count(skeleton, y, x)
        if deg >= 3:
            nodes['junctions'].append((int(y), int(x)))
        elif deg == 1:
            nodes['endpoints'].append((int(y), int(x)))
        elif deg == 0:
            nodes['isolated'].append((int(y), int(x)))
    
    return nodes


def process_mask_to_skeleton(
    mask: np.ndarray,
    min_area_px: int = 50,
) -> Tuple[np.ndarray, dict]:
    """
    Full pipeline: binary mask → cleaned → skeleton → nodes.
    
    Returns:
        skeleton: (H, W) binary array
        nodes: dict with 'junctions', 'endpoints', 'isolated'
    """
    cleaned = clean_binary_mask(mask, min_area_px=min_area_px)
    skeleton = skeletonize_mask(cleaned)
    nodes = extract_graph_nodes(skeleton)
    
    total_nodes = len(nodes['junctions']) + len(nodes['endpoints'])
    print(f"✓ Skeleton: {skeleton.sum()} px | Junctions: {len(nodes['junctions'])} | Endpoints: {len(nodes['endpoints'])}")
    
    return skeleton, nodes
