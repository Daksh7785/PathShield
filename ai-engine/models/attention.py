"""
Spatial and channel attention modules for occlusion-aware road segmentation.
These highlight the regions and features most relevant for road detection
even when roads are partially hidden.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class SpatialAttention(nn.Module):
    """
    2D spatial attention over ViT token grid.
    Learns to focus on regions that are likely to contain roads,
    including under occlusions by using global context.
    """

    def __init__(self, in_channels: int = 768, reduction: int = 8):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, in_channels // reduction, kernel_size=1)
        self.conv2 = nn.Conv2d(in_channels // reduction, 1, kernel_size=1)
        self.bn1 = nn.BatchNorm2d(in_channels // reduction)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (B, C, H, W) — reshaped ViT token features
        returns: (B, 1, H, W) attention weights
        """
        att = F.relu(self.bn1(self.conv1(x)))
        att = self.sigmoid(self.conv2(att))
        return att


class ChannelAttention(nn.Module):
    """
    Channel-wise attention (Squeeze-and-Excitation style).
    Reweights feature channels to emphasize road-relevant spectral bands.
    """

    def __init__(self, in_channels: int = 768, reduction: int = 16):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(in_channels, in_channels // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(in_channels // reduction, in_channels, bias=False),
        )
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (B, C, H, W)
        returns: (B, C, 1, 1) channel weights
        """
        B, C, _, _ = x.shape
        avg_feat = self.fc(self.avg_pool(x).view(B, C))
        max_feat = self.fc(self.max_pool(x).view(B, C))
        att = self.sigmoid(avg_feat + max_feat).view(B, C, 1, 1)
        return att
