from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class StressTestRequest(BaseModel):
    scenario_type: str  # "equipment_failure", "flood", "earthquake", "peak_traffic"
    removed_node_ids: Optional[List[int]] = []
    flood_bounds: Optional[List[float]] = []  # [minx, miny, maxx, maxy]
    epicenter: Optional[List[float]] = []      # [lng, lat]
    radius: Optional[float] = 0.015

class NodeImpact(BaseModel):
    node_id: int
    lcc_loss_pct: float
    path_increase_factor: float
    resilience_index: float
    critical: bool
    recommendation: str

class StressTestResponse(BaseModel):
    test_id: UUID
    city_id: UUID
    scenario_type: str
    affected_nodes_count: int
    resilience_index: float
    lcc_loss_percent: float
    path_increase_factor: float
    recommendation: str

    class Config:
        from_attributes = True
        populate_by_name = True
