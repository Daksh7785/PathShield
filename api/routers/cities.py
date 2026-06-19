from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List

from database.connection import get_db
from database.models import City

router = APIRouter()

@router.get("/")
async def list_cities(db: AsyncSession = Depends(get_db)):
    """List all available cities in the database."""
    result = await db.execute(select(City))
    cities = result.scalars().all()
    
    output = []
    for city in cities:
        output.append({
            "id": str(city.id),
            "name": city.name,
            "state": city.state,
            "country": city.country,
            "population": city.population,
            "area_sqkm": float(city.area_sqkm) if city.area_sqkm else 0.0,
            "zoom_level": city.zoom_level,
            "satellite_source": city.satellite_source,
            "resolution_m": float(city.resolution_m) if city.resolution_m else 0.0,
            "total_nodes": city.total_nodes,
            "total_edges": city.total_edges,
            "network_resilience_index": float(city.network_resilience_index) if city.network_resilience_index else 1.0
        })
    return output


@router.get("/{city_id}")
async def get_city(city_id: str, db: AsyncSession = Depends(get_db)):
    """Get details for a specific city by ID or by Name (e.g. 'bengaluru')."""
    # Check if city_id is a UUID or name
    try:
        uuid_val = UUID(city_id)
        stmt = select(City).where(City.id == uuid_val)
    except ValueError:
        # Fallback to query by name (case-insensitive)
        stmt = select(City).where(City.name.ilike(city_id))
        
    result = await db.execute(stmt)
    city = result.scalars().first()
    
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
        
    return {
        "id": str(city.id),
        "name": city.name,
        "state": city.state,
        "country": city.country,
        "population": city.population,
        "area_sqkm": float(city.area_sqkm) if city.area_sqkm else 0.0,
        "zoom_level": city.zoom_level,
        "satellite_source": city.satellite_source,
        "resolution_m": float(city.resolution_m) if city.resolution_m else 0.0,
        "total_nodes": city.total_nodes,
        "total_edges": city.total_edges,
        "avg_centrality": float(city.avg_centrality) if city.avg_centrality else 0.0,
        "network_resilience_index": float(city.network_resilience_index) if city.network_resilience_index else 1.0
    }
