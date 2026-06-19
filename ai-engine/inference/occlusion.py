"""
Synthetic Occlusion Generation Pipeline for satellite imagery.
Simulates realistic atmospheric, environmental, and structural occlusions:
- Shadows (from buildings and high-rise structures)
- Tree Canopies (foliage blocking roads)
- Clouds (varying density and transparency)
- Vehicles (bounding rectangles along road centerlines)
"""
import cv2
import numpy as np
from typing import Optional, Tuple, List


class SyntheticOcclusionGenerator:
    """Simulates various occlusion types on satellite images and labels."""

    def __init__(self, seed: Optional[int] = None):
        self.rng = np.random.default_rng(seed)

    def simulate_shadows(self, image: np.ndarray, intensity: float = 0.4, num_shadows: int = 4) -> np.ndarray:
        """
        Simulate building and terrain shadows.
        Creates elongated dark polygons/ellipses with smoothed Gaussian edges.
        """
        result = image.astype(np.float32).copy()
        H, W = image.shape[:2]

        for _ in range(num_shadows):
            cx = self.rng.integers(0, W)
            cy = self.rng.integers(0, H)
            # Elongated dimensions for shadows
            ax = self.rng.integers(30, 100)
            ay = self.rng.integers(10, 45)
            angle = self.rng.integers(0, 180)

            mask = np.zeros((H, W), dtype=np.float32)
            cv2.ellipse(mask, (cx, cy), (ax, ay), angle, 0, 360, 1.0, -1)
            
            # Smooth edges
            kernel_size = self.rng.choice([21, 31, 41])
            mask = cv2.GaussianBlur(mask, (kernel_size, kernel_size), kernel_size / 2)

            # Apply shadow multiplier (reduce intensity)
            alpha = 1.0 - (intensity * mask[:, :, np.newaxis])
            result *= alpha

        return np.clip(result, 0, 255).astype(np.uint8)

    def simulate_tree_canopy(self, image: np.ndarray, coverage: float = 0.5, num_patches: int = 6) -> np.ndarray:
        """
        Simulate forest and roadside tree canopies.
        Adds irregular green foliage structures onto the image.
        """
        result = image.astype(np.float32).copy()
        H, W = image.shape[:2]

        for _ in range(num_patches):
            cx = self.rng.integers(0, W)
            cy = self.rng.integers(0, H)
            radius = self.rng.integers(20, 70)

            mask = np.zeros((H, W), dtype=np.float32)
            cv2.circle(mask, (cx, cy), radius, 1.0, -1)

            # Add high-frequency noise to make canopy edges irregular
            noise = self.rng.uniform(-0.2, 0.2, (H, W)).astype(np.float32)
            mask = np.clip(mask + noise * mask, 0, 1)

            kernel_size = self.rng.choice([15, 25, 35])
            mask = cv2.GaussianBlur(mask, (kernel_size, kernel_size), kernel_size / 3)

            # Generate realistic green leaf colors
            foliage = np.zeros_like(result)
            foliage[:, :, 0] = self.rng.uniform(30, 60)   # R channel (low)
            foliage[:, :, 1] = self.rng.uniform(75, 120)  # G channel (high)
            foliage[:, :, 2] = self.rng.uniform(25, 55)   # B channel (low)

            alpha = (coverage * mask)[:, :, np.newaxis]
            result = (1.0 - alpha) * result + alpha * foliage

        return np.clip(result, 0, 255).astype(np.uint8)

    def simulate_clouds(self, image: np.ndarray, density: float = 0.3) -> np.ndarray:
        """
        Simulate cloud cover using fractal Perlin-like noise.
        Generates diffuse semi-transparent white/grey patches.
        """
        result = image.astype(np.float32).copy()
        H, W = image.shape[:2]

        # Generate low-res noise and upscale to get cloud structures
        scale = 8
        noise_small = self.rng.uniform(0, 1, (H // scale, W // scale)).astype(np.float32)
        noise = cv2.resize(noise_small, (W, H), interpolation=cv2.INTER_CUBIC)
        
        # Apply multiple octaves
        noise_small2 = self.rng.uniform(0, 1, (H // (scale * 2), W // (scale * 2))).astype(np.float32)
        noise2 = cv2.resize(noise_small2, (W, H), interpolation=cv2.INTER_CUBIC)
        
        noise = 0.7 * noise + 0.3 * noise2
        noise = cv2.GaussianBlur(noise, (51, 51), 25)
        
        # Normalize noise to full range to guarantee cloud generation
        noise = (noise - noise.min()) / (noise.max() - noise.min() + 1e-8)

        # Threshold to create cloud patches based on density
        cloud_mask = np.clip((noise - (1.0 - density)) / density, 0, 1)
        cloud_mask = cv2.GaussianBlur(cloud_mask, (31, 31), 15)

        # Cloud color (off-white/light grey)
        cloud_color = np.full_like(result, 230.0)
        
        alpha = cloud_mask[:, :, np.newaxis]
        result = (1.0 - alpha) * result + alpha * cloud_color

        return np.clip(result, 0, 255).astype(np.uint8)

    def simulate_vehicles(
        self,
        image: np.ndarray,
        mask: Optional[np.ndarray] = None,
        num_vehicles: int = 15
    ) -> np.ndarray:
        """
        Simulate vehicle occlusions on the road network.
        Draws bounding rectangles representing cars, buses, and trucks along the road centerline/mask.
        """
        result = image.copy()
        H, W = image.shape[:2]

        # Determine road locations
        if mask is not None and np.sum(mask > 127) > 50:
            road_y, road_x = np.where(mask > 127)
            indices = self.rng.choice(len(road_x), size=min(num_vehicles, len(road_x)), replace=False)
            centers = list(zip(road_x[indices], road_y[indices]))
        else:
            # Fallback: place along a random centerline diagonal/line
            centers = []
            for _ in range(num_vehicles):
                centers.append((self.rng.integers(10, W - 10), self.rng.integers(10, H - 10)))

        for cx, cy in centers:
            # Vehicle type: passenger car (small), truck/bus (long)
            v_type = self.rng.choice(["car", "truck"], p=[0.8, 0.2])
            if v_type == "car":
                length = self.rng.integers(6, 10)
                width = self.rng.integers(4, 6)
            else:
                length = self.rng.integers(12, 20)
                width = self.rng.integers(6, 8)

            # Random angle or parallel alignment (simulated)
            angle = self.rng.uniform(0, 180)
            
            # Select vehicle color (red, white, dark grey, blue, yellow)
            color = self.rng.choice([
                (220, 20, 20),    # Red
                (240, 240, 240),  # White
                (45, 45, 45),     # Dark Grey
                (30, 30, 200),    # Blue
                (220, 220, 10),   # Yellow
            ])
            color = (int(color[0]), int(color[1]), int(color[2]))

            # Create rotated rectangle box points
            rect = ((int(cx), int(cy)), (int(width), int(length)), float(angle))
            box = cv2.boxPoints(rect)
            box = np.intp(box)

            cv2.drawContours(result, [box], 0, color, -1)
            # Optional vehicle shadow / border
            cv2.drawContours(result, [box], 0, (10, 10, 10), 1)

        return result

    def generate_all_occlusions(self, image: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        """Apply a mixture of all occlusion types sequentially."""
        img = self.simulate_shadows(image)
        img = self.simulate_tree_canopy(img)
        img = self.simulate_clouds(img)
        img = self.simulate_vehicles(img, mask=mask)
        return img
