from pydantic import BaseModel
from typing import Optional
from uuid import UUID
import datetime

class CityBase(BaseModel):
    name: str
    country: str = "India"
    state: Optional[str] = None
    population: Optional[int] = None
    area_sqkm: Optional[float] = None
    zoom_level: Optional[int] = 13
    satellite_source: Optional[str] = None
    resolution_m: Optional[float] = None

class CityCreate(CityBase):
    pass

class CityResponse(CityBase):
    id: UUID
    total_nodes: int = 0
    total_edges: int = 0
    avg_centrality: float = 0.0
    network_resilience_index: float = 1.0
    created_at: datetime.datetime

    class Config:
        from_attributes = True
        populate_by_name = True
