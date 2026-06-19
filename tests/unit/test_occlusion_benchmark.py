"""
Unit tests for Synthetic Occlusion Generation and Model Benchmarking Engines.
Verifies occlusion-robust road extraction algorithms and metrics calculations.
"""
import numpy as np
import pytest
from inference.occlusion import SyntheticOcclusionGenerator
from inference.benchmark import ModelBenchmarkingEngine


def test_synthetic_occlusion_generator():
    """Verify that the occlusion generator runs and applies transformations without errors."""
    generator = SyntheticOcclusionGenerator(seed=42)
    
    # Create random test image (256x256x3 RGB)
    image = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
    mask = np.zeros((256, 256), dtype=np.uint8)
    mask[120:136, :] = 255  # Horizontal highway
    
    # 1. Test shadows
    shadowed = generator.simulate_shadows(image, num_shadows=2)
    assert shadowed.shape == image.shape
    assert not np.array_equal(shadowed, image)
    
    # 2. Test foliage
    foliage = generator.simulate_tree_canopy(image, num_patches=2)
    assert foliage.shape == image.shape
    assert not np.array_equal(foliage, image)
    
    # 3. Test clouds
    clouds = generator.simulate_clouds(image, density=0.2)
    assert clouds.shape == image.shape
    assert not np.array_equal(clouds, image)
    
    # 4. Test vehicles
    vehicles = generator.simulate_vehicles(image, mask=mask, num_vehicles=5)
    assert vehicles.shape == image.shape
    assert not np.array_equal(vehicles, image)
    
    # 5. E2E pipeline mixture
    all_occ = generator.generate_all_occlusions(image, mask=mask)
    assert all_occ.shape == image.shape
    assert not np.array_equal(all_occ, image)


def test_model_benchmarking_engine():
    """Verify that ModelBenchmarkingEngine evaluates all architectures and computes valid metrics."""
    engine = ModelBenchmarkingEngine(seed=42)
    
    # Create sample image and ground-truth mask
    image = np.full((256, 256, 3), 128, dtype=np.uint8)
    mask = np.zeros((256, 256), dtype=np.uint8)
    mask[100:156, :] = 255  # Large horizontal road
    
    # Run benchmark comparison
    results, best_model = engine.benchmark_all_models(image, mask)
    
    # Check that all 7 models were compared
    expected_models = {"U-Net", "UNet++", "DeepLabV3+", "SegFormer", "Swin Transformer", "Mask2Former", "RoadFormer"}
    assert set(results.keys()) == expected_models
    assert best_model in expected_models
    
    # Verify metrics structure and values range
    for model_name, metrics in results.items():
        for metric_name in ["IoU", "Dice", "Precision", "Recall", "F1", "RelaxedIoU", "OcclusionRecall", "AverageConfidence", "AverageUncertainty"]:
            assert metric_name in metrics
            assert 0.0 <= metrics[metric_name] <= 1.0


def test_uncertainty_map_entropy():
    """Verify that uncertainty maps calculate correct Shannon entropy bounds."""
    engine = ModelBenchmarkingEngine(seed=42)
    
    # Perfect certainty (all 0s or all 1s) should yield near 0 entropy
    certain_low = np.zeros((10, 10))
    certain_high = np.ones((10, 10))
    
    unc_low = engine.generate_uncertainty_map(certain_low)
    unc_high = engine.generate_uncertainty_map(certain_high)
    
    assert np.allclose(unc_low, 0.0, atol=1e-4)
    assert np.allclose(unc_high, 0.0, atol=1e-4)
    
    # Max uncertainty (probability 0.5) should yield exactly 1.0 entropy
    uncertain = np.full((10, 10), 0.5)
    unc_max = engine.generate_uncertainty_map(uncertain)
    
    assert np.allclose(unc_max, 1.0, atol=1e-4)
