from typing import Dict, Optional

class FeatureStore:
    """Centralized database interfaces for preprocessed ML features."""
    def __init__(self):
        # Local schema registry simulating central feature store entries
        self.road_features: Dict[str, Dict] = {}
        self.traffic_features: Dict[str, Dict] = {}
        self.demographics_features: Dict[str, Dict] = {}

    def register_road_features(self, segment_id: str, lanes: int, width_m: float, condition_score: float):
        self.road_features[segment_id] = {
            "lanes": lanes,
            "width_meters": width_m,
            "condition_score": condition_score
        }

    def get_road_features(self, segment_id: str) -> Optional[Dict]:
        return self.road_features.get(segment_id)

    def register_traffic_features(self, segment_id: str, historical_speeds: list[float], rush_hour_multiplier: float):
        self.traffic_features[segment_id] = {
            "historical_speeds": historical_speeds,
            "rush_hour_multiplier": rush_hour_multiplier
        }

    def get_traffic_features(self, segment_id: str) -> Optional[Dict]:
        return self.traffic_features.get(segment_id)

    def register_demographics(self, zone_id: str, population_density: float, ghsl_building_footprint_count: int):
        self.demographics_features[zone_id] = {
            "population_density_per_sqkm": population_density,
            "ghsl_building_footprints": ghsl_building_footprint_count
        }

    def get_demographics(self, zone_id: str) -> Optional[Dict]:
        return self.demographics_features.get(zone_id)
