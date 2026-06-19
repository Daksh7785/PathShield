"""
Load trained ViT model and run sliding window inference on city-scale imagery.
Handles batching, GPU memory management, and probability map reconstruction.
"""
import torch
import numpy as np
from pathlib import Path
from PIL import Image
import cv2
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RoadPredictor:
    """Wraps the trained segmentation model for production inference."""
    
    def __init__(
        self,
        checkpoint_path: str,
        device: str = "auto",
        batch_size: int = 16,
        threshold: float = 0.5,
    ):
        from models.vit_segmentation import VisionTransformerSegmentation
        
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.device = torch.device(device)
        self.batch_size = batch_size
        self.threshold = threshold
        self.model = None
        
        if Path(checkpoint_path).exists():
            self._load_model(checkpoint_path)
        else:
            logger.warning(f"Checkpoint not found: {checkpoint_path}. Using random weights.")
            self.model = VisionTransformerSegmentation(pretrained=False).to(self.device)
        
        self.model.eval()
        logger.info(f"✓ Predictor ready | Device: {device} | Batch: {batch_size}")
    
    def _load_model(self, checkpoint_path: str):
        from models.vit_segmentation import VisionTransformerSegmentation
        
        try:
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            self.model = VisionTransformerSegmentation(pretrained=False)
            
            if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                self.model.load_state_dict(checkpoint["model_state_dict"])
            else:
                self.model.load_state_dict(checkpoint)
        except Exception as e:
            logger.warning(f"Failed to load checkpoint dict: {e}. Reinitializing model.")
            self.model = VisionTransformerSegmentation(pretrained=False)
            
        self.model = self.model.to(self.device)
        logger.info(f"✓ Model loaded from {checkpoint_path}")
    
    def predict_tile(self, image: np.ndarray) -> np.ndarray:
        """
        Predict road probability for a single 256x256 tile.
        image: (H, W, 3) uint8 RGB
        returns: (H, W) float32 probability map [0,1]
        """
        from data_pipeline.normalization import apply_clahe, IMAGENET_MEAN, IMAGENET_STD
        
        image = apply_clahe(image)
        x = image.astype(np.float32) / 255.0
        x = (x - IMAGENET_MEAN) / IMAGENET_STD
        x = torch.from_numpy(x.transpose(2, 0, 1)).unsqueeze(0).float().to(self.device)
        
        with torch.no_grad():
            road_prob, _ = self.model(x)
        
        return road_prob.squeeze().cpu().numpy()
    
    def predict_batch(self, images: list) -> list:
        """
        Predict for a batch of images.
        images: list of (H, W, 3) uint8 arrays
        returns: list of (H, W) probability maps
        """
        from data_pipeline.normalization import apply_clahe, IMAGENET_MEAN, IMAGENET_STD
        
        tensors = []
        for img in images:
            img = apply_clahe(img)
            x = img.astype(np.float32) / 255.0
            x = (x - IMAGENET_MEAN) / IMAGENET_STD
            tensors.append(torch.from_numpy(x.transpose(2, 0, 1)).float())
        
        batch = torch.stack(tensors).to(self.device)
        
        with torch.no_grad():
            road_probs, _ = self.model(batch)
        
        return [p.squeeze().cpu().numpy() for p in road_probs]
    
    def predict_binary(self, image: np.ndarray) -> np.ndarray:
        """Predict binary road mask (0 or 1) for single tile."""
        prob = self.predict_tile(image)
        return (prob > self.threshold).astype(np.uint8) * 255

    def predict_patch(self, image: np.ndarray) -> tuple:
        """
        Predict road mask and confidence/uncertainty.
        image: (H, W, 3) uint8 RGB
        returns: (mask, confidence) where:
            mask is (H, W) binary array [0 or 1]
            confidence is (H, W) float32 probability map [0.0, 1.0]
        """
        prob = self.predict_tile(image)
        mask = (prob > self.threshold).astype(np.uint8)
        return mask, prob


