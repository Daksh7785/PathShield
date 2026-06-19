from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel

from database.connection import get_db
from database.models import City
from api.routers.analysis import load_graph_from_db
from analysis.routing import shortest_path, reroute_after_failure

router = APIRouter()


class RoutingRequest(BaseModel):
    source: int
    target: int
    avoid_nodes: Optional[List[int]] = []


@router.post("/{city_id}/path")
async def get_shortest_path(
    city_id: str,
    req: RoutingRequest,
    db: AsyncSession = Depends(get_db)
):
    """Compute shortest path between source and target, avoiding specific nodes."""
    try:
        city_uuid = UUID(city_id)
        stmt = select(City).where(City.id == city_uuid)
    except ValueError:
        stmt = select(City).where(City.name.ilike(city_id))
        
    city_res = await db.execute(stmt)
    city = city_res.scalars().first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    G = await load_graph_from_db(db, city.id)
    if len(G) == 0:
        raise HTTPException(status_code=400, detail="City network not loaded")

    if req.source not in G or req.target not in G:
        raise HTTPException(status_code=400, detail="Source or target node not found in city network")

    res = shortest_path(G, req.source, req.target, avoid_nodes=req.avoid_nodes)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
        
    return res


@router.post("/{city_id}/detour")
async def get_detour_overhead(
    city_id: str,
    req: RoutingRequest,
    db: AsyncSession = Depends(get_db)
):
    """Compare baseline routing distance against detour path under node failure."""
    try:
        city_uuid = UUID(city_id)
        stmt = select(City).where(City.id == city_uuid)
    except ValueError:
        stmt = select(City).where(City.name.ilike(city_id))
        
    city_res = await db.execute(stmt)
    city = city_res.scalars().first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    G = await load_graph_from_db(db, city.id)
    if len(G) == 0:
        raise HTTPException(status_code=400, detail="City network not loaded")

    res = reroute_after_failure(G, req.source, req.target, failed_nodes=req.avoid_nodes)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
        
    return res
