"""
Train script for Route Resilience Road Segmentation model.
Supports custom composite loss and ImageNet-pretrained ViT backbones.
"""
import os
import sys
import json
import argparse
import yaml
import numpy as np
import cv2
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
from torch.utils.data import DataLoader
from pathlib import Path

from models.vit_segmentation import VisionTransformerSegmentation
from models.losses import CompositeLoss
from data_pipeline.dataloader import get_dataloaders


def calculate_iou(pred: torch.Tensor, target: torch.Tensor, threshold: float = 0.5) -> float:
    """Calculate average Intersection-over-Union."""
    pred_bin = (pred > threshold).float()
    intersection = (pred_bin * target).sum()
    union = pred_bin.sum() + target.sum() - intersection
    if union == 0:
        return 1.0
    return (intersection / union).item()


def calculate_f1(pred: torch.Tensor, target: torch.Tensor, threshold: float = 0.5) -> float:
    """Calculate average F1 Score."""
    pred_bin = (pred > threshold).float()
    tp = (pred_bin * target).sum()
    fp = (pred_bin * (1 - target)).sum()
    fn = ((1 - pred_bin) * target).sum()
    if (2 * tp + fp + fn) == 0:
        return 1.0
    return (2 * tp / (2 * tp + fp + fn)).item()


def calculate_occlusion_iou(pred: torch.Tensor, target: torch.Tensor, occlusion_mask: torch.Tensor, threshold: float = 0.5) -> float:
    """Calculate IoU specifically on regions that are occluded."""
    pred_bin = (pred > threshold).float()
    # Mask out non-occluded regions
    pred_occ = pred_bin * occlusion_mask
    target_occ = target * occlusion_mask
    
    intersection = (pred_occ * target_occ).sum()
    union = pred_occ.sum() + target_occ.sum() - intersection
    if union == 0:
        return 1.0
    return (intersection / union).item()


def generate_synthetic_data(data_dir: str):
    """Generate 200 synthetic training tiles for testing/CI runs."""
    print("Generating synthetic dataset (200 tiles) for testing fallback...")
    data_path = Path(data_dir)
    
    dirs = [
        data_path / "processed" / "train" / "images",
        data_path / "processed" / "train" / "masks",
        data_path / "processed" / "val" / "images",
        data_path / "processed" / "val" / "masks"
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        
    rng = np.random.default_rng(42)
    
    # Generate 150 train, 50 val tiles
    for split, count, base_dir in [("train", 150, data_path / "processed" / "train"), ("val", 50, data_path / "processed" / "val")]:
        for i in range(count):
            img = rng.uniform(40, 100, (256, 256, 3)).astype(np.uint8)
            mask = np.zeros((256, 256), dtype=np.uint8)
            
            # Draw a simulated straight or curved road
            road_type = rng.choice(["h", "v", "diag"])
            thickness = rng.integers(6, 12)
            
            if road_type == "h":
                cy = rng.integers(100, 156)
                cv2.line(img, (0, cy), (256, cy), (120, 120, 120), thickness)
                cv2.line(mask, (0, cy), (256, cy), 255, thickness)
            elif road_type == "v":
                cx = rng.integers(100, 156)
                cv2.line(img, (cx, 0), (cx, 256), (120, 120, 120), thickness)
                cv2.line(mask, (cx, 0), (cx, 256), 255, thickness)
            else:
                cv2.line(img, (0, 0), (256, 256), (120, 120, 120), thickness)
                cv2.line(mask, (0, 0), (256, 256), 255, thickness)
                
            # Add Perlin-like foliage / shadow blobs to image only
            for _ in range(3):
                cx = rng.integers(20, 230)
                cy = rng.integers(20, 230)
                r = rng.integers(20, 50)
                cv2.circle(img, (cx, cy), r, (10, rng.integers(60, 90), 10), -1) # Forest canopy shadow
                
            filename = f"tile_{i:06d}.png"
            cv2.imwrite(str(base_dir / "images" / filename), img)
            cv2.imwrite(str(base_dir / "masks" / filename), mask)


def main():
    parser = argparse.ArgumentParser(description="Route Resilience Trainer")
    parser.add_argument("--config", type=str, default="configs/vit_b32.yaml", help="Path to config YAML")
    parser.add_argument("--data-dir", type=str, default="data/", help="Dataset root directory")
    parser.add_argument("--checkpoint-dir", type=str, default="models/checkpoints/", help="Checkpoint output folder")
    parser.add_argument("--resume", type=str, default=None, help="Path to checkpoint to resume training")
    parser.add_argument("--epochs", type=int, default=None, help="Override epochs")
    parser.add_argument("--batch-size", type=int, default=None, help="Override batch size")
    parser.add_argument("--lr", type=float, default=None, help="Override learning rate")
    parser.add_argument("--gpu", type=int, default=0, help="CUDA device index")
    parser.add_argument("--dry-run", action="store_true", help="Run 2 batches and exit (CI check)")
    
    args = parser.parse_args()
    
    # Load config
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)
        
    epochs = args.epochs if args.epochs is not None else config["training"]["epochs"]
    batch_size = args.batch_size if args.batch_size is not None else config["training"]["batch_size"]
    lr = args.lr if args.lr is not None else config["training"]["learning_rate"]
    
    # Set CUDA device
    if torch.cuda.is_available():
        device = torch.device(f"cuda:{args.gpu}")
        print(f"Using GPU device: {device}")
    else:
        device = torch.device("cpu")
        print("CUDA GPU not available. Training on CPU.")
        
    # Check dataset existence, fallback to generating mock data
    train_images_path = Path(args.data_dir) / "processed" / "train" / "images"
    if not train_images_path.exists() or len(os.listdir(train_images_path)) == 0:
        generate_synthetic_data(args.data_dir)
        
    # Get DataLoaders
    train_loader, val_loader = get_dataloaders(
        train_img_dir=os.path.join(args.data_dir, "processed", "train", "images"),
        train_mask_dir=os.path.join(args.data_dir, "processed", "train", "masks"),
        val_img_dir=os.path.join(args.data_dir, "processed", "val", "images"),
        val_mask_dir=os.path.join(args.data_dir, "processed", "val", "masks"),
        batch_size=batch_size
    )
    
    # Initialize model
    print("Initializing Vision Transformer model...")
    # Set pretrained=False if timm is offline/erroring
    try:
        model = VisionTransformerSegmentation(pretrained=config["model"]["pretrained"]).to(device)
    except Exception as e:
        print(f"Failed to load pretrained weights: {e}. Training from scratch.")
        model = VisionTransformerSegmentation(pretrained=False).to(device)
        
    # Loss, Optimizer & Scheduler
    w = config["training"]["loss_weights"]
    criterion = CompositeLoss(w["dice"], w["iou"], w["boundary"], w["connectivity"])
    
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=config["training"]["weight_decay"])
    scheduler = CosineAnnealingWarmRestarts(
        optimizer, 
        T_0=config["training"]["scheduler_t0"],
        eta_min=1e-6
    )
    
    # Optional mixed precision
    scaler = torch.cuda.amp.GradScaler(enabled=device.type == "cuda")
    
    start_epoch = 0
    best_val_loss = float("inf")
    training_log = []
    
    # Resume checkpoint
    if args.resume:
        if os.path.exists(args.resume):
            print(f"Resuming from checkpoint {args.resume}")
            checkpoint = torch.load(args.resume, map_location=device)
            model.load_state_dict(checkpoint["model_state_dict"])
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
            start_epoch = checkpoint["epoch"] + 1
            best_val_loss = checkpoint["val_loss"]
        else:
            print(f"Checkpoint file {args.resume} not found!")

    checkpoint_dir = Path(args.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    print("Beginning training loop...")
    early_stop_count = 0
    patience = config["training"]["early_stopping_patience"]
    
    for epoch in range(start_epoch, epochs):
        model.train()
        train_losses = []
        
        for batch_idx, (images, masks, _) in enumerate(train_loader):
            images = images.to(device)
            masks = masks.to(device)
            
            optimizer.zero_grad()
            
            with torch.cuda.amp.autocast(enabled=device.type == "cuda"):
                pred_masks, pred_edges = model(images)
                loss_dict = criterion(pred_masks, masks)
                loss = loss_dict["total"]
                
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), config["training"]["gradient_clip_norm"])
            scaler.step(optimizer)
            scaler.update()
            
            train_losses.append(loss.item())
            
            if batch_idx % 50 == 0:
                print(f"Epoch {epoch:02d} [{batch_idx:03d}/{len(train_loader):03d}] | "
                      f"Total Loss: {loss.item():.4f} (Dice: {loss_dict['dice']:.4f}, IoU: {loss_dict['iou']:.4f})")
                      
            if args.dry_run and batch_idx >= 1:
                break
                
        # Validate
        model.eval()
        val_losses = []
        val_ious = []
        val_f1s = []
        
        with torch.no_grad():
            for batch_idx, (images, masks, _) in enumerate(val_loader):
                images = images.to(device)
                masks = masks.to(device)
                
                pred_masks, _ = model(images)
                loss_dict = criterion(pred_masks, masks)
                val_losses.append(loss_dict["total"].item())
                
                iou = calculate_iou(pred_masks, masks)
                f1 = calculate_f1(pred_masks, masks)
                val_ious.append(iou)
                val_f1s.append(f1)
                
                if args.dry_run and batch_idx >= 1:
                    break
                    
        avg_train_loss = float(np.mean(train_losses))
        avg_val_loss = float(np.mean(val_losses))
        avg_val_iou = float(np.mean(val_ious))
        avg_val_f1 = float(np.mean(val_f1s))
        
        print(f"--- Epoch {epoch:02d} Summary | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f} | Val IoU: {avg_val_iou:.1f}% | Val F1: {avg_val_f1:.1f}%")
        
        # Log epoch values
        epoch_log = {
            "epoch": epoch,
            "train_loss": avg_train_loss,
            "val_loss": avg_val_loss,
            "val_iou": avg_val_iou,
            "val_f1": avg_val_f1
        }
        training_log.append(epoch_log)
        
        # Save training logs to JSON
        with open(checkpoint_dir / "training_log.json", "w") as f:
            json.dump(training_log, f, indent=2)
            
        scheduler.step(epoch)
        
        # Save best checkpoint
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            early_stop_count = 0
            
            checkpoint = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
                "val_loss": avg_val_loss,
                "val_iou": avg_val_iou,
                "config": config,
            }
            torch.save(checkpoint, checkpoint_dir / "model_best.pth")
            print(f"⭐ New best validation loss: {best_val_loss:.4f}. Saved checkpoint model_best.pth")
        else:
            early_stop_count += 1
            
        # Every 10 epochs, save regular checkpoint
        if epoch % 10 == 0:
            torch.save(model.state_dict(), checkpoint_dir / f"checkpoint_epoch_{epoch}.pth")
            
        # Early stopping check
        if early_stop_count >= patience:
            print(f"Early stopping triggered after {patience} epochs without improvement.")
            break
            
        if args.dry_run:
            print("Dry-run complete. Exiting training script.")
            break
            
    print("\n╔══════════════════════════════╗")
    print("║  TRAINING COMPLETE           ║")
    print(f"║  Best Epoch: {start_epoch + np.argmin([x['val_loss'] for x in training_log])}              ║")
    print(f"║  Val Loss:   {best_val_loss:.4f}          ║")
    print(f"║  Val IoU:    {np.max([x['val_iou'] for x in training_log])*100:.1f}%           ║")
    print(f"║  Checkpoint: {checkpoint_dir / 'model_best.pth'} ║")
    print("╚══════════════════════════════╝")

if __name__ == "__main__":
    main()
