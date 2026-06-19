"""
Normalize satellite imagery patches using CLAHE + ImageNet statistics.
"""
import cv2
import numpy as np
from typing import Tuple

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def apply_clahe(image: np.ndarray, clip_limit: float = 2.0, grid_size: Tuple = (8, 8)) -> np.ndarray:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) per channel.
    Enhances road visibility in shadowed regions.
    """
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
    result = image.copy()
    
    if len(image.shape) == 3:
        # Convert to LAB, apply CLAHE to L channel
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    else:
        result = clahe.apply(image)
    
    return result


def normalize_imagenet(image: np.ndarray) -> np.ndarray:
    """
    Normalize uint8 RGB image [0,255] to float32 using ImageNet stats.
    Output shape: (C, H, W) — PyTorch convention.
    """
    if image.dtype != np.float32:
        image = image.astype(np.float32) / 255.0
    
    normalized = (image - IMAGENET_MEAN) / IMAGENET_STD  # (H, W, 3)
    return normalized.transpose(2, 0, 1)  # (3, H, W)


def denormalize_imagenet(tensor: np.ndarray) -> np.ndarray:
    """Reverse ImageNet normalization to uint8 for visualization."""
    image = tensor.transpose(1, 2, 0)  # (H, W, 3)
    image = (image * IMAGENET_STD + IMAGENET_MEAN)
    image = np.clip(image * 255, 0, 255).astype(np.uint8)
    return image
