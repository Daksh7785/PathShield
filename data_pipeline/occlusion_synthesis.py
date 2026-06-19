"""
Synthesize realistic occlusions on satellite imagery for training data augmentation.
Creates shadows (buildings), foliage (tree canopy), and cloud cover.
"""
import cv2
import numpy as np
from typing import Optional


class OcclusionAugmenter:
    """Add realistic occlusions to satellite imagery patches."""

    def __init__(self, seed: Optional[int] = None):
        self.rng = np.random.default_rng(seed)

    def add_shadows(self, image: np.ndarray, intensity: float = 0.35, num_shadows: int = 3) -> np.ndarray:
        """
        Add Gaussian shadow blobs simulating building shadows.
        Shadows are darker, elongated ellipses with soft edges.
        """
        result = image.astype(np.float32).copy()
        H, W = image.shape[:2]

        for _ in range(num_shadows):
            cx = self.rng.integers(0, W)
            cy = self.rng.integers(0, H)
            ax = self.rng.integers(20, 80)
            ay = self.rng.integers(10, 40)
            angle = self.rng.integers(0, 180)

            mask = np.zeros((H, W), dtype=np.float32)
            cv2.ellipse(mask, (cx, cy), (ax, ay), angle, 0, 360, 1.0, -1)
            mask = cv2.GaussianBlur(mask, (31, 31), 15)
            
            alpha = (1.0 - intensity * mask[:, :, np.newaxis])
            result = result * alpha

        return np.clip(result, 0, 255).astype(np.uint8)

    def add_foliage(self, image: np.ndarray, coverage: float = 0.4, num_patches: int = 5) -> np.ndarray:
        """
        Add green noise patches simulating tree canopy cover.
        Uses Perlin-like noise tinted green.
        """
        result = image.copy()
        H, W = image.shape[:2]

        for _ in range(num_patches):
            cx = self.rng.integers(0, W)
            cy = self.rng.integers(0, H)
            radius = self.rng.integers(15, 60)

            mask = np.zeros((H, W), dtype=np.float32)
            cv2.circle(mask, (cx, cy), radius, 1.0, -1)
            mask = cv2.GaussianBlur(mask, (21, 21), 10)

            # Green tinted overlay
            green_overlay = np.zeros_like(result, dtype=np.float32)
            green_noise = self.rng.uniform(60, 120, (H, W)).astype(np.float32)
            green_overlay[:, :, 0] = green_noise * 0.3   # R: low
            green_overlay[:, :, 1] = green_noise * 0.9   # G: high
            green_overlay[:, :, 2] = green_noise * 0.2   # B: low

            alpha = (coverage * mask)[:, :, np.newaxis]
            result = ((1 - alpha) * result.astype(np.float32) + alpha * green_overlay)

        return np.clip(result, 0, 255).astype(np.uint8)

    def add_clouds(self, image: np.ndarray, density: float = 0.25) -> np.ndarray:
        """
        Add cloud patches using random noise smoothed with large kernel.
        White/grey blobs of varying opacity.
        """
        result = image.astype(np.float32).copy()
        H, W = image.shape[:2]

        noise = self.rng.uniform(0, 1, (H // 4, W // 4)).astype(np.float32)
        cloud_mask = cv2.resize(noise, (W, H), interpolation=cv2.INTER_CUBIC)
        cloud_mask = cv2.GaussianBlur(cloud_mask, (41, 41), 20)
        cloud_mask = (cloud_mask > (1 - density)).astype(np.float32)
        cloud_mask = cv2.GaussianBlur(cloud_mask, (21, 21), 10)

        white = np.full_like(result, 220, dtype=np.float32)
        alpha = cloud_mask[:, :, np.newaxis]
        result = (1 - alpha) * result + alpha * white

        return np.clip(result, 0, 255).astype(np.uint8)

    def __call__(self, image: np.ndarray, occlusion_types: Optional[list] = None) -> np.ndarray:
        """
        Apply a random combination of occlusions.
        occlusion_types: list of ['shadow', 'foliage', 'cloud'] or None for random selection
        """
        if occlusion_types is None:
            occlusion_types = []
            if self.rng.random() < 0.6:
                occlusion_types.append('shadow')
            if self.rng.random() < 0.5:
                occlusion_types.append('foliage')
            if self.rng.random() < 0.2:
                occlusion_types.append('cloud')

        result = image.copy()
        for occ in occlusion_types:
            if occ == 'shadow':
                result = self.add_shadows(result)
            elif occ == 'foliage':
                result = self.add_foliage(result)
            elif occ == 'cloud':
                result = self.add_clouds(result)

        return result
