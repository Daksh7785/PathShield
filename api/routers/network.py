import os
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import Optional
import redis

from database.connection import get_db
from database.models import City, Node, Edge
from topology.skeletonization import process_mask_to_skeleton
from topology.healing import heal_topology
from topology.graph_builder import skeleton_to_graph, graph_to_geojson

router = APIRouter()
logger = logging.getLogger("route-resilience.network")

# Optional Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    cache = redis.from_url(REDIS_URL, decode_responses=True)
except Exception:
    cache = None
    logger.warning("Redis cache is offline. Caching disabled.")


def safe_float(val) -> float:
    return float(val) if val is not None else 0.0


@router.get("/{city_id}/geojson")
async def get_network_geojson(city_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the full network road graph (nodes & edges) as GeoJSON.
    Caches results in Redis with a 1-hour TTL.
    """
    cache_key = f"network:{city_id}:geojson"
    if cache:
        try:
            cached_data = cache.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis cache read error: {e}")

    # Fetch city
    try:
        uuid_val = UUID(city_id)
        stmt = select(City).where(City.id == uuid_val)
    except ValueError:
        stmt = select(City).where(City.name.ilike(city_id))
    city_res = await db.execute(stmt)
    city = city_res.scalars().first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    
    # Query nodes & edges
    nodes_res = await db.execute(select(Node).where(Node.city_id == city.id))
    nodes = nodes_res.scalars().all()
    
    edges_res = await db.execute(select(Edge).where(Edge.city_id == city.id))
    edges = edges_res.scalars().all()

    features = []
    # Serialize Nodes to GeoJSON Points
    for n in nodes:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [safe_float(n.longitude), safe_float(n.latitude)]
            },
            "properties": {
                "id": int(n.id),
                "node_type": n.node_type,
                "degree": n.degree,
                "betweenness_centrality": safe_float(n.betweenness_centrality),
                "criticality_score": safe_float(n.criticality_score),
                "criticality_rank": n.criticality_rank,
                "is_gateway": n.is_gateway,
                "city_id": str(city.id)
            }
        })

    # Serialize Edges to GeoJSON LineStrings
    for e in edges:
        # Since geometries might be stored in PostGIS format, let's extract coords from the geometry attribute if available,
        # or fallback to direct coordinates from database nodes
        # If we use GeoAlchemy2, shape(e.geom) is typically a Shapely LineString. Let's do a safe coordinate extraction:
        coords = []
        try:
            from shapely import wkb
            # Convert binary geometry
            geom_shape = wkb.loads(bytes(e.geom.data))
            coords = list(geom_shape.coords)
        except Exception:
            # Fallback direct line between source and target
            pass
            
        if not coords:
            # Try to get source and target coordinates from current nodes list
            src_node = next((n for n in nodes if n.id == e.source_id), None)
            tgt_node = next((n for n in nodes if n.id == e.target_id), None)
            if src_node and tgt_node:
                coords = [
                    [safe_float(src_node.longitude), safe_float(src_node.latitude)],
                    [safe_float(tgt_node.longitude), safe_float(tgt_node.latitude)]
                ]

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[safe_float(coord[0]), safe_float(coord[1])] for coord in coords]
            },
            "properties": {
                "id": int(e.id),
                "source": int(e.source_id),
                "target": int(e.target_id),
                "length_meters": safe_float(e.length_meters),
                "road_type": e.road_type,
                "is_healing_edge": e.is_healing_edge,
                "confidence": safe_float(e.confidence)
            }
        })

    geojson = {"type": "FeatureCollection", "features": features}

    if cache:
        try:
            cache.setex(cache_key, 3600, json.dumps(geojson))
        except Exception as e:
            logger.warning(f"Redis cache write error: {e}")

    return geojson


@router.get("/{city_id}/nodes")
async def get_nodes(
    city_id: str,
    min_centrality: Optional[float] = 0.0,
    is_gateway: Optional[bool] = None,
    limit: Optional[int] = 50,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve nodes within a city based on filters."""
    try:
        uuid_val = UUID(city_id)
        stmt = select(City).where(City.id == uuid_val)
    except ValueError:
        stmt = select(City).where(City.name.ilike(city_id))
    city_res = await db.execute(stmt)
    city = city_res.scalars().first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    query = select(Node).where(
        Node.city_id == city.id,
        Node.betweenness_centrality >= min_centrality
    )
    if is_gateway is not None:
        query = query.where(Node.is_gateway == is_gateway)

    query = query.order_by(Node.betweenness_centrality.desc()).limit(limit)
    res = await db.execute(query)
    nodes = res.scalars().all()

    return [{
        "id": int(n.id),
        "longitude": safe_float(n.longitude),
        "latitude": safe_float(n.latitude),
        "node_type": n.node_type,
        "degree": n.degree,
        "betweenness_centrality": safe_float(n.betweenness_centrality),
        "criticality_score": safe_float(n.criticality_score),
        "criticality_rank": n.criticality_rank,
        "is_gateway": n.is_gateway
    } for n in nodes]
