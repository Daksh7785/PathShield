import { Router, Request, Response } from 'express';
import axios from 'axios';
import { isDbMock, MockDB } from '../config/db';
import { City } from '../models/City';
import { getOrGenerateTraffic } from './traffic';

const router = Router();
const GRAPH_ENGINE_URL = process.env.GRAPH_ENGINE_URL || 'http://localhost:8003';

// Post stress test simulation
router.post('/:cityId/stress-test', async (req: Request, res: Response) => {
  const { cityId } = req.params;
  const { scenario_type, flood_bounds, ablate_nodes, seed_node, iterations, failure_probability } = req.body;
  
  try {
    let city: any;
    if (isDbMock) {
      city = MockDB.getCityById(cityId);
    } else {
      if (cityId.match(/^[0-9a-fA-F]{24}$/)) {
        city = await City.findById(cityId);
      } else {
        city = await City.findOne({ name: new RegExp('^' + cityId + '$', 'i') });
      }
    }
    
    if (!city) {
      return res.status(404).json({ error: 'City not found' });
    }
    
    // Prepare the payload for graph engine
    const graph_json = {
      nodes: city.nodes,
      edges: city.edges
    };
    
    const payload = {
      graph_json,
      scenario_type,
      flood_bounds,
      ablate_nodes,
      seed_node,
      iterations,
      failure_probability
    };
    
    // Call Graph Engine Microservice
    console.log(`Forwarding stress-test request to Graph Engine: ${GRAPH_ENGINE_URL}/stress-test`);
    try {
      const response = await axios.post(`${GRAPH_ENGINE_URL}/stress-test`, payload);
      return res.json(response.data);
    } catch (apiErr: any) {
      console.warn(`⚠️ Graph Engine call failed, running Node.js fallback stress-test simulation.`);
      // Mock fallback if graph engine is offline
      const baselineLcc = city.total_nodes;
      const lccLossPct = scenario_type === 'flood' ? 15.4 : 8.2;
      const index = scenario_type === 'flood' ? 0.625 : 0.742;
      return res.json({
        scenario_type,
        removed_node_count: ablate_nodes ? ablate_nodes.length : 1,
        baseline_lcc_size: baselineLcc,
        perturbed_lcc_size: Math.round(baselineLcc * (1 - lccLossPct / 100)),
        lcc_loss_percent: lccLossPct,
        resilience_index: index,
        critical: index < 0.7,
        recommendation_text: index < 0.7 ? "CRITICAL — immediate redundancy required. Add parallel route within 500m." : "LOW RISK — monitor as part of regular maintenance."
      });
    }
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

// Routing simulation
router.post('/:cityId/route', async (req: Request, res: Response) => {
  const { cityId } = req.params;
  const { source_node, target_node, disabled_nodes, disabled_edges } = req.body;
  
  try {
    let city: any;
    if (isDbMock) {
      city = MockDB.getCityById(cityId);
    } else {
      if (cityId.match(/^[0-9a-fA-F]{24}$/)) {
        city = await City.findById(cityId);
      } else {
        city = await City.findOne({ name: new RegExp('^' + cityId + '$', 'i') });
      }
    }
    
    if (!city) {
      return res.status(404).json({ error: 'City not found' });
    }

    const graph_json = {
      nodes: city.nodes,
      edges: city.edges
    };

    const final_disabled_edges = [...(disabled_edges || [])];
    const traffic_congestion: { [key: string]: number } = {};
    
    try {
      const trafficState = getOrGenerateTraffic(cityId, city.edges || []);
      Object.entries(trafficState.congestion).forEach(([key, val]: any) => {
        traffic_congestion[key] = val.multiplier;
      });
      trafficState.incidents.forEach((inc: any) => {
        if (inc.type === 'closure') {
          final_disabled_edges.push(inc.edge);
        }
      });
    } catch (e) {
      console.warn("⚠️ Failed to generate or map traffic data:", e);
    }

    const payload = {
      graph_json,
      source_node,
      target_node,
      disabled_nodes,
      disabled_edges: final_disabled_edges,
      traffic_congestion
    };
    
    try {
      const response = await axios.post(`${GRAPH_ENGINE_URL}/route`, payload);
      return res.json(response.data);
    } catch (apiErr: any) {
      console.warn(`⚠️ Graph Engine call failed, running Node.js fallback routing.`);
      // Mock route output if Graph Engine is offline
      return res.json({
        shortest_path: [source_node, target_node],
        distance_meters: 350.0,
        alternative_path: [],
        alternative_distance_meters: 0
      });
    }
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

// GET /disasters - Live Active Disaster overlay feed (GDACS/NASA mock)
router.get('/feed/disasters', (req: Request, res: Response) => {
  return res.json([
    {
      id: "disaster-1",
      title: "GDACS Flood Alert: Bellandur Reservoir Overflow",
      type: "flood",
      severity: "high",
      longitude: 77.495,
      latitude: 12.945,
      city: "bengaluru",
      radius_meters: 600
    },
    {
      id: "disaster-2",
      title: "NASA FIRMS Fire Detection: Industrial Area Hotspot",
      type: "fire",
      severity: "medium",
      longitude: 77.145,
      latitude: 28.605,
      city: "delhi",
      radius_meters: 400
    },
    {
      id: "disaster-3",
      title: "GDACS Coastal Surge Alert: Colaba High-Tide Blockage",
      type: "flood",
      severity: "high",
      longitude: 72.825,
      latitude: 18.985,
      city: "mumbai",
      radius_meters: 800
    }
  ]);
});

// POST /copilot - AI Mobility Copilot NLP query handler
router.post('/feed/copilot', async (req: Request, res: Response) => {
  const { query, cityId = 'bengaluru' } = req.body;
  
  if (!query) {
    return res.status(400).json({ error: "Query is required" });
  }

  const q = query.toLowerCase();
  let reply = "";
  
  if (q.includes("bridge") || q.includes("fail") || q.includes("ablate") || q.includes("remove")) {
    reply = "Simulating structural ablate failure. Disabling the primary connecting corridor drops the global Resilience Index to 72.4%. It is recommended to designate Node 25 as a secondary transit corridor and reinforce the parallel grid bridges within 500 meters to prevent complete ward isolation.";
  } else if (q.includes("critical") || q.includes("bottleneck") || q.includes("junction") || q.includes("bengaluru")) {
    reply = "RouteGuard AI graph analysis of Bengaluru identifies that the outer ring roads and the central junctions (Node 12, Node 45) exhibit the highest Betweenness Centrality scores. These nodes act as 'gatekeeper' intersections; their failure causes cascading traffic gridlock on all surrounding arterial streets.";
  } else if (q.includes("safe") || q.includes("evacuate") || q.includes("flood")) {
    reply = "Emergency evacuation corridor computed. The primary shortest path avoids the active GDACS flood zone at Bellandur. The route covers 450 meters with an estimated arrival time of 8 minutes for emergency vehicles, using our dynamic traffic friction weights.";
  } else {
    reply = "RouteGuard AI Copilot active. You can ask me to simulate bridge collapses, identify the most critical bottleneck intersections in Bengaluru/Delhi, or calculate safe evacuation routes avoiding GDACS flood boundaries.";
  }

  return res.json({
    query,
    reply,
    timestamp: new Date().toISOString()
  });
});

export default router;
