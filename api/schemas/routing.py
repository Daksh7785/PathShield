from pydantic import BaseModel
from typing import List, Optional

class RoutingRequest(BaseModel):
    source: int
    target: int
    avoid_nodes: Optional[List[int]] = []

class RoutingResponse(BaseModel):
    path: List[int]
    geometry: List[List[float]]
    distance_meters: float
    turns: int
