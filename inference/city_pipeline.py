"""
End-to-end pipeline: satellite image → road network graph → database.
Orchestrates: tiling → inference → healing → graph building → DB insert.
"""
import os
import json
import asyncio
import numpy as np
from pathlib import Path
from PIL import Image
import logging
import time

logger = logging.getLogger(__name__)


class CityProcessor:
    """Orchestrates the full processing pipeline for one city."""
    
    def __init__(
        self,
        city_id: str,
        city_config: dict,
        predictor,
        db_session=None,
        output_dir: str = "data/processed/",
    ):
        self.city_id = city_id
        self.city_config = city_config
        self.predictor = predictor
        self.db_session = db_session
        self.output_dir = Path(output_dir) / city_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run(self, satellite_image_path: str) -> dict:
        """
        Full pipeline: image → graph → saved to disk/DB.
        
        Returns summary dict with timing and metrics.
        """
        start = time.time()
        results = {}
        
        print(f"\n{'='*60}")
        print(f"Processing {self.city_config.get('name', self.city_id)}")
        print(f"{'='*60}")
        
        # Step 1: Tile image
        print("\n[1/5] Tiling satellite image...")
        from data_pipeline.tiling import tile_geotiff
        tile_dir = str(self.output_dir / "tiles")
        metadata = tile_geotiff(satellite_image_path, tile_dir)
        results["total_tiles"] = metadata["total_tiles"]
        
        # Step 2: Run inference
        print(f"\n[2/5] Running inference on {metadata['total_tiles']} tiles...")
        prob_dir = str(self.output_dir / "probabilities")
        os.makedirs(prob_dir, exist_ok=True)
        
        tile_files = sorted([t["filename"] for t in metadata["tiles"]])
        
        # Batch inference
        all_probs = {}
        
        for i in range(0, len(tile_files), self.predictor.batch_size):
            batch_files = tile_files[i:i + self.predictor.batch_size]
            batch_images = []
            
            for fname in batch_files:
                img_path = os.path.join(tile_dir, fname)
                if os.path.exists(img_path):
                    img = np.array(Image.open(img_path).convert("RGB"))
                    batch_images.append(img)
                else:
                    batch_images.append(np.zeros((256, 256, 3), dtype=np.uint8))
            
            probs = self.predictor.predict_batch(batch_images)
            
            for fname, prob in zip(batch_files, probs):
                out_path = os.path.join(prob_dir, fname.replace(".png", "_prob.npy"))
                np.save(out_path, prob)
                all_probs[fname] = prob
            
            if (i // self.predictor.batch_size) % 10 == 0:
                print(f"  Processed {min(i + self.predictor.batch_size, len(tile_files))}/{len(tile_files)} tiles")
        
        # Step 3: Reconstruct full probability map
        print("\n[3/5] Reconstructing city-scale probability map...")
        from data_pipeline.tiling import reconstruct_from_tiles
        full_prob_path = str(self.output_dir / "probability_map.png")
        
        # Save predictions as PNGs for reconstruction
        for tile_info in metadata["tiles"]:
            fname = tile_info["filename"]
            pred_path = os.path.join(tile_dir, fname.replace(".png", "_pred.png"))
            if fname in all_probs:
                prob_img = (all_probs[fname] * 255).astype(np.uint8)
                Image.fromarray(prob_img).save(pred_path)
        
        H = metadata.get("height", 1024)
        W = metadata.get("width", 1024)
        prob_map = reconstruct_from_tiles(tile_dir, full_prob_path, (H, W))
        
        # Binarize
        binary_mask = (prob_map > 0.5).astype(np.uint8) * 255
        binary_path = str(self.output_dir / "binary_mask.png")
        Image.fromarray(binary_mask).save(binary_path)
        results["binary_mask_path"] = binary_path
        
        # Step 4: Build topology graph
        print("\n[4/5] Building road network graph...")
        from topology.skeletonization import process_mask_to_skeleton
        from topology.healing import heal_topology
        from topology.graph_builder import skeleton_to_graph, graph_to_geojson
        
        skeleton, nodes = process_mask_to_skeleton(binary_mask)
        healed = heal_topology(skeleton, nodes["endpoints"], nodes["junctions"])
        
        bounds = tuple(self.city_config.get("bounds", [77.45, 12.85, 77.75, 13.10]))
        G = skeleton_to_graph(healed, nodes, bounds, city_id=self.city_id)
        
        # Step 5: Calculate centrality
        print("\n[5/5] Calculating betweenness centrality...")
        from analysis.centrality import calculate_betweenness_centrality, composite_criticality_score
        calculate_betweenness_centrality(G)
        composite_criticality_score(G)
        
        # Export GeoJSON
        geojson_path = str(self.output_dir / "network.geojson")
        graph_to_geojson(G, geojson_path)
        
        elapsed = time.time() - start
        results.update({
            "city_id": self.city_id,
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "geojson_path": geojson_path,
            "processing_time_s": round(elapsed, 2),
        })
        
        print(f"\n{'='*60}")
        print(f"✓ {self.city_config.get('name', self.city_id)} processing complete!")
        print(f"  Nodes: {results['nodes']:,} | Edges: {results['edges']:,}")
        print(f"  Time: {elapsed:.1f}s")
        print(f"  Output: {geojson_path}")
        print(f"{'='*60}\n")
        
        return results, G
