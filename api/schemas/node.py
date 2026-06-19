from pydantic import BaseModel
from typing import Optional, Dict
from uuid import UUID

class NodeBase(BaseModel):
    longitude: float
    latitude: float
    node_type: str = "intersection"
    is_gateway: bool = False
    degree: int = 0
    betweenness_centrality: float = 0.0
    closeness_centrality: float = 0.0
    criticality_score: float = 0.0
    confidence: float = 1.0

class NodeResponse(NodeBase):
    id: int
    city_id: UUID
    criticality_rank: Optional[int] = None
    is_isolated: bool = False

    class Config:
        from_attributes = True
        populate_by_name = True
