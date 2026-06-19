import os
import sys
import base64
from io import BytesIO
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
from PIL import Image
import torch

# Ensure current folder is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from inference.predictor import RoadPredictor
from models.vit_segmentation import VisionTransformerSegmentation
from inference.orchestrator import AIOrchestrator

app = FastAPI(title="PathShield AI Engine", version="1.0.0")
orchestrator = AIOrchestrator()


# Lazy load predictor
_predictor = None

def get_predictor():
    global _predictor
    if _predictor is None:
        checkpoint_path = os.getenv("MODEL_CHECKPOINT_PATH", "models/checkpoints/model_best.pth")
        # If checkpoint doesn't exist, build model and save a dummy checkpoint
        if not os.path.exists(checkpoint_path):
            os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
            model = VisionTransformerSegmentation(pretrained=False)
            torch.save(model.state_dict(), checkpoint_path)
            print(f"Created dummy model checkpoint at {checkpoint_path}")
            
        _predictor = RoadPredictor(
            checkpoint_path=checkpoint_path,
            device="cpu"
        )
    return _predictor

class PredictRequest(BaseModel):
    image_base64: str

class PredictResponse(BaseModel):
    mask_base64: str
    confidence_base64: str
    average_confidence: float

@app.get("/health")
def health():
    return {"status": "healthy", "service": "ai-engine"}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    try:
        # Decode base64 image
        img_data = base64.b64decode(req.image_base64)
        img = Image.open(BytesIO(img_data)).convert("RGB")
        img_np = np.array(img)
        
        predictor = get_predictor()
        # Run prediction
        # predictor.predict_patch expects an RGB image patch [H, W, 3] and returns (mask, confidence)
        mask, conf = predictor.predict_patch(img_np)
        
        # Convert output to base64
        mask_pil = Image.fromarray((mask * 255).astype(np.uint8))
        conf_pil = Image.fromarray((conf * 255).astype(np.uint8))
        
        mask_buffer = BytesIO()
        mask_pil.save(mask_buffer, format="PNG")
        mask_b64 = base64.b64encode(mask_buffer.getvalue()).decode("utf-8")
        
        conf_buffer = BytesIO()
        conf_pil.save(conf_buffer, format="PNG")
        conf_b64 = base64.b64encode(conf_buffer.getvalue()).decode("utf-8")
        
        return PredictResponse(
            mask_base64=mask_b64,
            confidence_base64=conf_b64,
            average_confidence=float(np.mean(conf))
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

def make_synthetic_patch() -> tuple:
    import cv2
    rng = np.random.default_rng(42)
    img = rng.uniform(40, 100, (256, 256, 3)).astype(np.uint8)
    mask = np.zeros((256, 256), dtype=np.uint8)
    # Draw simulated road lines
    cv2.line(img, (0, 128), (256, 128), (120, 120, 120), 10)
    cv2.line(mask, (0, 128), (256, 128), 255, 10)
    return img, mask

@app.get("/benchmark")
def benchmark():
    from inference.benchmark import ModelBenchmarkingEngine
    try:
        img, mask = make_synthetic_patch()
        engine = ModelBenchmarkingEngine(seed=42)
        results, best_model = engine.benchmark_all_models(img, mask)
        return {
            "models": results,
            "selected_model": best_model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmarking failed: {str(e)}")


class OrchestrateRequest(BaseModel):
    task_type: str
    width: int
    height: int
    min_confidence: Optional[float] = 0.85

class RecordDriftRequest(BaseModel):
    calculated_iou: float

class RollbackRequest(BaseModel):
    model_name: str
    target_version: str

@app.post("/orchestrate")
def post_orchestrate(req: OrchestrateRequest):
    return orchestrator.route_inference(req.task_type, (req.width, req.height), req.min_confidence)

@app.post("/drift/record")
def post_record_drift(req: RecordDriftRequest):
    return orchestrator.drift_detector.record_prediction(req.calculated_iou)

@app.post("/registry/rollback")
def post_rollback(req: RollbackRequest):
    try:
        msg = orchestrator.registry.rollback_model(req.model_name, req.target_version)
        return {"status": "success", "message": msg}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

