"""
Unit tests for Minimum Spanning Tree and angular-vector gap healing heuristics.
"""
import numpy as np
from topology.healing import (
    compute_local_direction,
    angular_compatibility,
    heal_topology
)


def test_heals_straight_gap():
    """Verify that collinear segments separated by a small gap are connected."""
    skeleton = np.zeros((100, 100), dtype=np.uint8)
    skeleton[50, 10:40] = 1   # Segment 1
    skeleton[50, 60:90] = 1   # Segment 2
    
    # Endpoints at (50, 39) and (50, 60)
    endpoints = [(50, 39), (50, 60)]
    junctions = []
    
    # Bridge distance is 21px (< 50px limit) and they are perfectly collinear
    healed = heal_topology(skeleton, endpoints, junctions, max_gap_px=50, angular_threshold=35.0)
    
    # The gap at (50, 45) should now be filled (value == 1)
    assert healed[50, 45] == 1, "Failed to heal collinear road gap"


def test_rejects_perpendicular_bridge():
    """Verify that endpoints at perpendicular angles are NOT bridged."""
    skeleton = np.zeros((100, 100), dtype=np.uint8)
    skeleton[50, 10:40] = 1   # Horizontal segment ending at (50, 39)
    skeleton[10:40, 50] = 1   # Vertical segment ending at (39, 50)
    
    endpoints = [(50, 39), (39, 50)]
    junctions = []
    
    healed = heal_topology(skeleton, endpoints, junctions, max_gap_px=50, angular_threshold=35.0)
    
    # Since they are perpendicular (90 degrees), they should not connect
    # Check midpoint between endpoints: (44, 44)
    assert healed[44, 44] == 0, "Bridged incompatible perpendicular segments"


def test_max_gap_respected():
    """Verify that gaps exceeding max_gap_px are ignored."""
    skeleton = np.zeros((150, 150), dtype=np.uint8)
    skeleton[50, 10:40] = 1    # Ends at (50, 39)
    skeleton[50, 120:140] = 1  # Starts at (50, 120)
    
    endpoints = [(50, 39), (50, 120)]
    junctions = []
    
    # Distance is 81px (> 50px limit)
    healed = heal_topology(skeleton, endpoints, junctions, max_gap_px=50)
    
    # Midpoint should remain empty
    assert healed[50, 80] == 0, "Bridged a gap exceeding the max distance constraint"
