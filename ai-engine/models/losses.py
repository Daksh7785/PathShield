"""
Composite loss function for road segmentation.
Combines Dice, IoU, Boundary, and Connectivity losses for
topologically aware training — especially under occlusions.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class DiceLoss(nn.Module):
    """Dice loss — handles class imbalance (roads << non-roads)."""

    def __init__(self, smooth: float = 1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        pred_flat = pred.view(-1)
        target_flat = target.view(-1)
        intersection = (pred_flat * target_flat).sum()
        dice = (2.0 * intersection + self.smooth) / (pred_flat.sum() + target_flat.sum() + self.smooth)
        return 1.0 - dice


class IoULoss(nn.Module):
    """Jaccard/IoU loss — geometric accuracy of segmentation."""

    def __init__(self, smooth: float = 1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        pred_flat = pred.view(-1)
        target_flat = target.view(-1)
        intersection = (pred_flat * target_flat).sum()
        union = pred_flat.sum() + target_flat.sum() - intersection
        iou = (intersection + self.smooth) / (union + self.smooth)
        return 1.0 - iou


class BoundaryLoss(nn.Module):
    """
    Boundary-aware loss — weights errors near road edges more heavily.
    Uses distance transform or Sobel kernels to identify boundary regions.
    """

    def __init__(self):
        super().__init__()
        # Sobel kernels for edge detection
        self.register_buffer('sobel_x', torch.tensor(
            [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=torch.float32
        ).view(1, 1, 3, 3))
        self.register_buffer('sobel_y', torch.tensor(
            [[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=torch.float32
        ).view(1, 1, 3, 3))

    def get_boundary(self, mask: torch.Tensor) -> torch.Tensor:
        """Extract boundary pixels from binary mask."""
        boundary_x = F.conv2d(mask, self.sobel_x, padding=1)
        boundary_y = F.conv2d(mask, self.sobel_y, padding=1)
        boundary = torch.sqrt(boundary_x ** 2 + boundary_y ** 2 + 1e-8)
        return (boundary > 0.1).float()

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        # Get boundary maps
        target_boundary = self.get_boundary(target)
        pred_boundary = self.get_boundary(pred)
        
        # Weight regular loss higher at boundaries
        boundary_weight = 1.0 + 5.0 * target_boundary
        bce = F.binary_cross_entropy(pred, target, weight=boundary_weight, reduction='mean')
        
        # Also penalize boundary mis-detection
        boundary_bce = F.binary_cross_entropy(
            pred_boundary.clamp(0, 1),
            target_boundary,
            reduction='mean'
        )
        
        return 0.7 * bce + 0.3 * boundary_bce


class ConnectivityLoss(nn.Module):
    """
    Connectivity loss — penalizes disconnected road predictions.
    Uses morphological dilation to check spatial connectivity.
    """

    def __init__(self):
        super().__init__()
        # 3x3 dilation kernel
        self.register_buffer('dil_kernel', torch.ones(1, 1, 3, 3))

    def forward(self, pred: torch.Tensor) -> torch.Tensor:
        """
        Penalize isolated road pixels that have no neighbors.
        pred: (B, 1, H, W) predicted road probabilities
        """
        # Dilate to find neighbors
        dilated = F.conv2d(pred, self.dil_kernel, padding=1)
        dilated = torch.clamp(dilated / 9.0, 0, 1)
        
        # Isolated pixels: predicted road but few neighbors
        isolation_penalty = pred * (1.0 - dilated)
        
        return isolation_penalty.mean()


class CompositeLoss(nn.Module):
    """
    Weighted combination of all losses.
    Default weights from paper experiments: Dice(0.4) + IoU(0.3) + Boundary(0.2) + Connectivity(0.1)
    """

    def __init__(self, w_dice=0.4, w_iou=0.3, w_boundary=0.2, w_connectivity=0.1):
        super().__init__()
        self.dice = DiceLoss()
        self.iou = IoULoss()
        self.boundary = BoundaryLoss()
        self.connectivity = ConnectivityLoss()
        self.w_dice = w_dice
        self.w_iou = w_iou
        self.w_boundary = w_boundary
        self.w_connectivity = w_connectivity

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> dict:
        l_dice = self.dice(pred, target)
        l_iou = self.iou(pred, target)
        l_boundary = self.boundary(pred, target)
        l_connectivity = self.connectivity(pred)

        total = (self.w_dice * l_dice + self.w_iou * l_iou +
                 self.w_boundary * l_boundary + self.w_connectivity * l_connectivity)

        return {
            "total": total,
            "dice": l_dice.item(),
            "iou": l_iou.item(),
            "boundary": l_boundary.item(),
            "connectivity": l_connectivity.item(),
        }
