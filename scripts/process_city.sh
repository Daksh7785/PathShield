#!/bin/bash
set -e
CITY=${1:-bengaluru}
IMG=${2:-data/raw/${CITY}.tif}
echo "🛰️ Processing $CITY from $IMG"

python -c "
import yaml
from inference.predictor import RoadPredictor
from inference.city_pipeline import CityProcessor

with open('configs/cities.yaml') as f:
    config = yaml.safe_load(f)['cities']

predictor = RoadPredictor(
    checkpoint_path='models/checkpoints/model_best.pth',
    device='auto',
    batch_size=16,
)

processor = CityProcessor(
    city_id='$CITY',
    city_config=config['$CITY'],
    predictor=predictor,
)

results, G = processor.run('$IMG')
print(results)
"

echo "✓ Done! Network saved to data/processed/$CITY/network.geojson"
