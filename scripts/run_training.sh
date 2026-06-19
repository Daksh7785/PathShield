#!/bin/bash
set -e
echo "🚀 Starting Route Resilience model training..."
cd "$(dirname "$0")/.."

python train.py \
  --config configs/vit_b32.yaml \
  --data-dir data/ \
  --checkpoint-dir models/checkpoints/ \
  --gpu 0

echo "✓ Training complete!"
