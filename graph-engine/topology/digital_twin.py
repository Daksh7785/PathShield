import time
from typing import Dict, List, Optional

class DigitalTwinStore:
    """Stores and replays historical state snapshots of city infrastructure networks."""
    def __init__(self):
        # In-memory snapshot database: city_id -> List[Dict]
        self.snapshots: Dict[str, List[Dict]] = {}

    def capture_snapshot(self, city_id: str, nodes_count: int, edges_count: int, active_hazards_count: int, traffic_layers: Dict[str, float]) -> Dict:
        snapshot = {
            "timestamp": time.time(),
            "nodes_count": nodes_count,
            "edges_count": edges_count,
            "active_hazards_count": active_hazards_count,
            "traffic_layers": traffic_layers.copy()
        }
        if city_id not in self.snapshots:
            self.snapshots[city_id] = []
        self.snapshots[city_id].append(snapshot)
        return snapshot

    def get_timeline(self, city_id: str) -> List[Dict]:
        return self.snapshots.get(city_id, [])

    def replay_state_at(self, city_id: str, target_time: float) -> Optional[Dict]:
        timeline = self.get_timeline(city_id)
        if not timeline:
            return None
        # Find the snapshot closest to target_time without exceeding it
        best_match = None
        for snap in timeline:
            if snap["timestamp"] <= target_time:
                if best_match is None or snap["timestamp"] > best_match["timestamp"]:
                    best_match = snap
        return best_match if best_match else timeline[0]
