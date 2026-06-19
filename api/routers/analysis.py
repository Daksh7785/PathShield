import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID, uuid4
from typing import List, Optional
from pydantic import BaseModel
from shapely import wkb

from database.connection import get_db
from database.models import City, Node, Edge, StressTestResult
from analysis.stress_test import StressTestEngine
from analysis.scenarios import run_scenario
import networkx as nx

router = APIRouter()


class StressTestRequest(BaseModel):
    scenario_type: str  # "equipment_failure", "flood", "earthquake", "peak_traffic"
    removed_node_ids: Optional[List[int]] = []
    flood_bounds: Optional[List[float]] = []  # [minx, miny, maxx, maxy]
    epicenter: Optional[List[float]] = []      # [lng, lat]
    radius: Optional[float] = 0.015


async def load_graph_from_db(db: AsyncSession, city_id: UUID) -> nx.Graph:
    """Load the nodes and edges from PostgreSQL/PostGIS into a NetworkX Graph."""
    # Query nodes
    nodes_res = await db.execute(select(Node).where(Node.city_id == city_id))
    nodes = nodes_res.scalars().all()
    
    # Query edges
    edges_res = await db.execute(select(Edge).where(Edge.city_id == city_id))
    edges = edges_res.scalars().all()

    G = nx.Graph()
    
    for n in nodes:
        G.add_node(
            int(n.id),
            longitude=float(n.longitude) if n.longitude else 0.0,
            latitude=float(n.latitude) if n.latitude else 0.0,
            pos=(float(n.longitude) if n.longitude else 0.0, float(n.latitude) if n.latitude else 0.0),
            betweenness_centrality=float(n.betweenness_centrality) if n.betweenness_centrality else 0.0,
            criticality_score=float(n.criticality_score) if n.criticality_score else 0.0,
            degree=n.degree,
            is_gateway=n.is_gateway
        )
        
    for e in edges:
        G.add_edge(
            int(e.source_id),
            int(e.target_id),
            weight=float(e.length_meters) if e.length_meters else 1.0,
            length_meters=float(e.length_meters) if e.length_meters else 1.0,
            is_healing_edge=e.is_healing_edge
        )
        
    return G


@router.post("/{city_id}/stress-test")
async def run_stress_test(
    city_id: str,
    req: StressTestRequest,
    db: AsyncSession = Depends(get_db)
):
    """Run a stress test scenario and log the results."""
    # Fetch city
    try:
        city_uuid = UUID(city_id)
        stmt = select(City).where(City.id == city_uuid)
    except ValueError:
        stmt = select(City).where(City.name.ilike(city_id))
        
    city_res = await db.execute(stmt)
    city = city_res.scalars().first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    # Load Graph
    G = await load_graph_from_db(db, city.id)
    if len(G) == 0:
        raise HTTPException(status_code=400, detail="City has no road network nodes loaded")

    start_time = time.time()
    
    # Configure parameters
    kwargs = {}
    if req.scenario_type == "flood" and req.flood_bounds:
        kwargs["bounds"] = tuple(req.flood_bounds)
    elif req.scenario_type == "earthquake" and req.epicenter:
        kwargs["epicenter"] = tuple(req.epicenter)
        kwargs["radius"] = req.radius
    elif req.scenario_type == "equipment_failure":
        # Custom ablation of specific nodes
        engine = StressTestEngine(G)
        res = engine.ablate_nodes(req.removed_node_ids)
        res_index = res["resilience_index"]
        
        # Save one representative record
        test_uuid = uuid4()
        primary_node = req.removed_node_ids[0] if req.removed_node_ids else None
        
        db_res = StressTestResult(
            city_id=city.id,
            test_id=test_uuid,
            removed_node_id=primary_node,
            removed_node_count=len(req.removed_node_ids),
            scenario_type="equipment_failure",
            baseline_lcc_size=res["baseline_lcc_size"],
            perturbed_lcc_size=res["perturbed_lcc_size"],
            lcc_loss_percent=res["lcc_loss_percent"],
            baseline_avg_path_length=res["baseline_avg_path_length"],
            perturbed_avg_path_length=res["perturbed_avg_path_length"],
            path_increase_factor=res["path_increase_factor"] if res["path_increase_factor"] != float('inf') else 999.0,
            baseline_efficiency=res["baseline_efficiency"],
            perturbed_efficiency=res["perturbed_efficiency"],
            resilience_index=res_index,
            critical=res["critical"],
            recommendation_text=res["recommendation_text"],
            execution_time_ms=int((time.time() - start_time) * 1000)
        )
        db.add(db_res)
        await db.flush()
        
        return {
            "test_id": str(test_uuid),
            "city_id": str(city.id),
            "scenario_type": "equipment_failure",
            "resilience_index": res_index,
            "lcc_loss_percent": res["lcc_loss_percent"],
            "path_increase_factor": res["path_increase_factor"],
            "recommendation": res["recommendation_text"]
        }

    # Run dispatch scenario
    res = run_scenario(G, req.scenario_type, **kwargs)
    test_uuid = uuid4()
    
    db_res = StressTestResult(
        city_id=city.id,
        test_id=test_uuid,
        removed_node_count=res["affected_nodes_count"],
        scenario_type=req.scenario_type,
        baseline_lcc_size=G.number_of_nodes(),  # fallback baseline
        perturbed_lcc_size=int(G.number_of_nodes() - res["affected_nodes_count"]),
        lcc_loss_percent=res["lcc_loss"],
        path_increase_factor=res["path_increase"] if res["path_increase"] != float('inf') else 999.0,
        resilience_index=res["resilience_index"],
        critical=res["resilience_index"] < 0.7,
        recommendation_text=res["recommendations"],
        execution_time_ms=int((time.time() - start_time) * 1000)
    )
    db.add(db_res)
    await db.flush()

    return {
        "test_id": str(test_uuid),
        "city_id": str(city.id),
        "scenario_type": req.scenario_type,
        "affected_nodes_count": res["affected_nodes_count"],
        "resilience_index": res["resilience_index"],
        "lcc_loss_percent": res["lcc_loss"],
        "path_increase_factor": res["path_increase"],
        "recommendation": res["recommendations"]
    }


@router.get("/{city_id}/vulnerability-report")
async def get_vulnerability_report(city_id: str, db: AsyncSession = Depends(get_db)):
    """Analyze high-betweenness intersections and rank their structural vulnerability."""
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
        return []

    engine = StressTestEngine(G)
    report = engine.full_vulnerability_report(top_n=20)
    
    return report
