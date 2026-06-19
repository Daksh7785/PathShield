"""
Post-processing operations for road segmentation masks,
including morphological cleanup and hysteresis thresholding.
"""
import numpy as np
import cv2


def apply_morphological_cleanup(
    binary_mask: np.ndarray, 
    open_size: int = 3, 
    close_size: int = 5
) -> np.ndarray:
    """Apply morphological opening and closing to remove speckles and fill gaps."""
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_size, open_size))
    cleaned = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel_open)
    
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_size, close_size))
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel_close)
    
    return cleaned


def threshold_with_hysteresis(
    prob_map: np.ndarray, 
    high: float = 0.7, 
    low: float = 0.3
) -> np.ndarray:
    """
    Apply double thresholding (hysteresis).
    Keeps all pixels above 'high', plus any pixels above 'low' that are 
    8-connected to pixels above 'high'.
    """
    high_mask = (prob_map > high).astype(np.uint8) * 255
    low_mask = (prob_map > low).astype(np.uint8) * 255
    
    # Use OpenCV floodFill to find connected components from high seeds
    output = np.zeros_like(high_mask)
    H, W = prob_map.shape
    
    # Find contours/seeds in the high threshold mask
    contours, _ = cv2.findContours(high_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        for pt in cnt:
            x, y = pt[0]
            if 0 <= x < W and 0 <= y < H and low_mask[y, x] == 255 and output[y, x] == 0:
                # Flood fill on the low_mask to keep all connected components
                cv2.floodFill(low_mask, None, (x, y), 127)
                
    # Pixels marked with 127 are connected to high-confidence seeds
    output[low_mask == 127] = 255
    return output


def apply_crf(image: np.ndarray, probabilities: np.ndarray, n_iters: int = 5) -> np.ndarray:
    """
    Apply dense CRF refinement. Fallback gracefully if pydensecrf is not installed.
    """
    try:
        import pydensecrf.densecrf as dcrf
        from pydensecrf.utils import unary_from_softmax, create_pairwise_bilateral, create_pairwise_gaussian
        
        H, W = probabilities.shape
        # Convert to 2-class probabilities
        probs = np.stack([1.0 - probabilities, probabilities], axis=0) # shape (2, H, W)
        
        # Dense CRF setup
        d = dcrf.DenseCRF2D(W, H, 2)
        unary = unary_from_softmax(probs)
        d.setUnaryEnergy(unary)
        
        # Pairwise potentials
        feats_gauss = create_pairwise_gaussian(sdims=(3, 3), shape=(H, W))
        d.addPairwiseEnergy(feats_gauss, compat=3, kernel=dcrf.DIAG_KERNEL, normalization=dcrf.NORMALIZE_BEFORE)
        
        feats_bilat = create_pairwise_bilateral(sdims=(10, 10), schan=(13, 13, 13), img=image, chdim=2)
        d.addPairwiseEnergy(feats_bilat, compat=10, kernel=dcrf.DIAG_KERNEL, normalization=dcrf.NORMALIZE_BEFORE)
        
        # Inference
        Q = d.inference(n_iters)
        map_ = np.argmax(Q, axis=0).reshape((H, W))
        
        return (map_ * 255).astype(np.uint8)
        
    except ImportError:
        # Graceful fallback: return simple thresholded mask
        return (probabilities > 0.5).astype(np.uint8) * 255
