import time
from typing import Dict, List, Optional, Tuple

class ModelRegistry:
    """Manages registered Vision/ML models, versions, and deployment status."""
    def __init__(self):
        self.models = {
            "segformer-road-extractor": {
                "v1.0": {"status": "archived", "iou_score": 0.84, "params_m": 84},
                "v1.1": {"status": "production", "iou_score": 0.89, "params_m": 84},
                "v1.2-beta": {"status": "testing", "iou_score": 0.91, "params_m": 84}
            },
            "vit-shadow-healer": {
                "v1.0": {"status": "production", "iou_score": 0.82, "params_m": 120}
            }
        }

    def get_active_model(self, model_name: str) -> Tuple[str, Dict]:
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not registered.")
        for version, attrs in self.models[model_name].items():
            if attrs["status"] == "production":
                return version, attrs
        raise RuntimeError(f"No production version for {model_name}.")

    def rollback_model(self, model_name: str, target_version: str):
        if model_name not in self.models or target_version not in self.models[model_name]:
            raise ValueError("Target model version not found.")
        for version in self.models[model_name]:
            if self.models[model_name][version]["status"] == "production":
                self.models[model_name][version]["status"] = "archived"
        self.models[model_name][target_version]["status"] = "production"
        return f"Successfully rolled back {model_name} to {target_version}."


class DriftDetector:
    """Monitors sliding-window metrics to detect model input/feature drift."""
    def __init__(self, target_iou_threshold: float = 0.80, window_size: int = 100):
        self.target_iou_threshold = target_iou_threshold
        self.window_size = window_size
        self.history: List[float] = []

    def record_prediction(self, calculated_iou: float) -> Dict:
        self.history.append(calculated_iou)
        if len(self.history) > self.window_size:
            self.history.pop(0)
            
        current_mean = sum(self.history) / len(self.history)
        drift_detected = False
        
        # Trigger drift warning if moving average drops below target
        if len(self.history) >= 10 and current_mean < self.target_iou_threshold:
            drift_detected = True
            
        return {
            "window_size_current": len(self.history),
            "average_iou": round(current_mean, 4),
            "drift_detected": drift_detected,
            "status": "DRIFT_WARNING" if drift_detected else "STABLE"
        }


class AIOrchestrator:
    """Orchestrates model inference routing, fallback strategies, and GPU allocations."""
    def __init__(self):
        self.registry = ModelRegistry()
        self.drift_detector = DriftDetector()

    def route_inference(self, task_type: str, image_size: Tuple[int, int], min_confidence: float = 0.85) -> Dict:
        # GPU Allocation Simulator
        gpu_id = 0 if image_size[0] * image_size[1] > 1024 * 1024 else -1
        device = f"cuda:{gpu_id}" if gpu_id >= 0 else "cpu"
        
        # Determine model
        model_name = "segformer-road-extractor" if task_type == "extraction" else "vit-shadow-healer"
        try:
            version, meta = self.registry.get_active_model(model_name)
        except Exception as e:
            return {"error": str(e)}
            
        # Fallback model strategy: if production model does not satisfy confidence constraints
        selected_version = version
        using_fallback = False
        
        if meta["iou_score"] < min_confidence:
            # Fall back to high-capacity testing model if available
            test_version = "v1.2-beta"
            if test_version in self.registry.models[model_name]:
                selected_version = test_version
                using_fallback = True
                
        return {
            "device": device,
            "allocated_gpu": gpu_id >= 0,
            "target_model": model_name,
            "active_version": selected_version,
            "using_fallback_model": using_fallback,
            "expected_confidence": self.registry.models[model_name][selected_version]["iou_score"],
            "timestamp": time.time()
        }
