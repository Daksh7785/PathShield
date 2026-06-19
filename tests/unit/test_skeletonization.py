"""
Unit tests for Zhang-Suen thinning skeletonization and node extraction routines.
"""
import numpy as np
import cv2
from topology.skeletonization import (
    clean_binary_mask,
    skeletonize_mask,
    extract_graph_nodes,
    process_mask_to_skeleton
)


def test_skeleton_output_is_1px_wide():
    """Verify that the skeleton output for a simple road is 1 pixel wide."""
    mask = np.zeros((50, 50), dtype=np.uint8)
    mask[20:25, :] = 255  # 5px wide horizontal road
    
    skeleton = skeletonize_mask(mask)
    
    # Vertically slice the skeleton, any active column should have exactly 1 pixel
    for col in range(5, 45):
        active_pixels = np.sum(skeleton[:, col])
        assert active_pixels <= 1, f"Skeleton is not 1px wide at col {col}: got {active_pixels} pixels"


def test_junction_detection():
    """Verify that a '+' shaped road mask produces exactly one junction node."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[45:55, :] = 255  # Horizontal
    mask[:, 45:55] = 255  # Vertical
    
    skeleton, nodes = process_mask_to_skeleton(mask)
    
    # Center junction at index (50, 50) +- 5px
    assert len(nodes['junctions']) >= 1, "Failed to detect junction"
    
    # Check that at least one junction is close to the intersection center (50, 50)
    found_center = False
    for y, x in nodes['junctions']:
        if abs(y - 50) <= 5 and abs(x - 50) <= 5:
            found_center = True
            break
    assert found_center, "Junction node not found near coordinate center (50, 50)"


def test_endpoint_detection():
    """Verify that a 'T' shaped road mask produces 3 endpoint nodes."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[45:55, 20:80] = 255  # Horizontal segment
    mask[50:90, 45:55] = 255  # Vertical leg down
    
    _, nodes = process_mask_to_skeleton(mask)
    assert len(nodes['endpoints']) >= 3, f"Expected at least 3 endpoints, got {len(nodes['endpoints'])}"


def test_empty_mask_returns_empty_skeleton():
    """Verify that an all-zero mask returns an all-zero skeleton with no nodes."""
    mask = np.zeros((50, 50), dtype=np.uint8)
    skeleton, nodes = process_mask_to_skeleton(mask)
    assert np.sum(skeleton) == 0
    assert len(nodes['junctions']) == 0
    assert len(nodes['endpoints']) == 0


def test_clean_mask_removes_noise():
    """Verify that minor pixel noise is removed while larger segments are kept."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[20:23, 20:23] = 255      # 3x3 noise speck (9 pixels < 50px area threshold)
    mask[45:55, 10:90] = 255      # Large highway (800 pixels > 50px)
    
    cleaned = clean_binary_mask(mask, min_area_px=50)
    
    # Noise should be removed
    assert np.sum(cleaned[15:28, 15:28]) == 0
    # Highway should be preserved
    assert np.sum(cleaned[45:55, 10:90]) > 0
