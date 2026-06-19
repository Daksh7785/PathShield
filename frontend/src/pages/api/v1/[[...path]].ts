import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';

// Haversine distance in meters
function haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371e3;
  const phi1 = (lat1 * Math.PI) / 180;
  const phi2 = (lat2 * Math.PI) / 180;
  const deltaPhi = ((lat2 - lat1) * Math.PI) / 180;
  const deltaLambda = ((lon2 - lon1) * Math.PI) / 180;

  const a =
    Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
}

// Convert Overpass road elements to Node/Edge graph topology
function overpassToNetwork(elements: any[]): { nodes: any[]; edges: any[] } {
  const coordToId: { [key: string]: number } = {};
  const nodes: any[] = [];
  const edges: any[] = [];

  const coordCounts: { [key: string]: number } = {};
  for (const el of elements) {
    if (el.type === 'way' && el.geometry) {
      for (const geom of el.geometry) {
        const key = `${geom.lon.toFixed(6)},${geom.lat.toFixed(6)}`;
        coordCounts[key] = (coordCounts[key] || 0) + 1;
      }
    }
  }

  let nodeIdCounter = 1;

  for (const el of elements) {
    if (el.type === 'way' && el.geometry && el.geometry.length >= 2) {
      const coords = el.geometry;
      let currentPath: any[] = [];

      for (let i = 0; i < coords.length; i++) {
        const pt = coords[i];
        const key = `${pt.lon.toFixed(6)},${pt.lat.toFixed(6)}`;
        currentPath.push({ lon: pt.lon, lat: pt.lat, key });

        const isJunction = coordCounts[key] > 1;
        const isEndpoint = i === 0 || i === coords.length - 1;

        if ((isJunction || isEndpoint) && currentPath.length > 1) {
          const startPt = currentPath[0];
          const endPt = currentPath[currentPath.length - 1];

          for (const ptObj of [startPt, endPt]) {
            if (!coordToId[ptObj.key]) {
              coordToId[ptObj.key] = nodeIdCounter;
              nodes.push({
                id: nodeIdCounter,
                longitude: ptObj.lon,
                latitude: ptObj.lat,
                node_type: coordCounts[ptObj.key] > 1 ? 'intersection' : 'endpoint',
                degree: 0,
                betweenness_centrality: parseFloat((Math.random() * 0.1).toFixed(4)),
                closeness_centrality: parseFloat((Math.random() * 0.1).toFixed(4)),
                is_gateway: false
              });
              nodeIdCounter++;
            }
          }

          const u = coordToId[startPt.key];
          const v = coordToId[endPt.key];

          if (u !== v) {
            let dist = haversineDistance(startPt.lat, startPt.lon, endPt.lat, endPt.lon);
            dist = Math.max(5.0, dist);
            edges.push({
              source: u,
              target: v,
              length_meters: parseFloat(dist.toFixed(2)),
              confidence: 1.0,
              is_healing_edge: false
            });
          }

          currentPath = [pt];
        }
      }
    }
  }

  for (const edge of edges) {
    const u = edge.source;
    const v = edge.target;
    for (const node of nodes) {
      if (node.id === u || node.id === v) {
        node.degree++;
      }
    }
  }

  for (const node of nodes) {
    node.is_gateway = node.degree === 1;
  }

  return { nodes, edges };
}

// Generate synthetic 8x8 spatial grid
function generateFallbackNetwork(bbox: number[]): { nodes: any[]; edges: any[] } {
  const [minLat, minLng, maxLat, maxLng] = bbox;
  const nodes: any[] = [];
  const edges: any[] = [];
  const cols = 8;
  const rows = 8;

  const xCoords = Array.from({ length: cols }, (_, i) => minLng + (i * (maxLng - minLng)) / (cols - 1));
  const yCoords = Array.from({ length: rows }, (_, i) => minLat + (i * (maxLat - minLat)) / (rows - 1));

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const id = r * cols + c + 1;
      nodes.push({
        id,
        longitude: xCoords[c],
        latitude: yCoords[r],
        node_type: (r % 2 === 0 && c % 2 === 0) ? 'intersection' : 'endpoint',
        degree: 0,
        betweenness_centrality: parseFloat((Math.random() * 0.1).toFixed(4)),
        closeness_centrality: parseFloat((Math.random() * 0.1).toFixed(4)),
        is_gateway: false
      });
    }
  }

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const curr = r * cols + c + 1;
      if (c + 1 < cols) {
        const dist = haversineDistance(yCoords[r], xCoords[c], yCoords[r], xCoords[c + 1]);
        edges.push({
          source: curr,
          target: curr + 1,
          length_meters: parseFloat(Math.max(5.0, dist).toFixed(2)),
          confidence: 1.0,
          is_healing_edge: false
        });
      }
      if (r + 1 < rows) {
        const dist = haversineDistance(yCoords[r], xCoords[c], yCoords[r + 1], xCoords[c]);
        edges.push({
          source: curr,
          target: curr + cols,
          length_meters: parseFloat(Math.max(5.0, dist).toFixed(2)),
          confidence: 1.0,
          is_healing_edge: false
        });
      }
    }
  }

  for (const edge of edges) {
    const u = edge.source;
    const v = edge.target;
    for (const node of nodes) {
      if (node.id === u || node.id === v) {
        node.degree++;
      }
    }
  }

  for (const node of nodes) {
    node.is_gateway = node.degree === 1;
  }

  return { nodes, edges };
}

// Generate seeded mock networks (10x10 grids)
function generateMockNetwork(minx: number, miny: number, maxx: number, maxy: number) {
  const nodes: any[] = [];
  const edges: any[] = [];
  const cols = 10;
  const rows = 10;

  const x_coords = Array.from({ length: cols }, (_, i) => minx + (i * (maxx - minx)) / (cols - 1));
  const y_coords = Array.from({ length: rows }, (_, i) => miny + (i * (maxy - miny)) / (rows - 1));

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const id = r * cols + c;
      const lng = x_coords[c] + (Math.random() - 0.5) * 0.001;
      const lat = y_coords[r] + (Math.random() - 0.5) * 0.001;
      nodes.push({
        id,
        longitude: lng,
        latitude: lat,
        degree: 0,
        node_type: (r % 3 === 0 && c % 3 === 0) ? 'intersection' : 'endpoint',
        betweenness_centrality: parseFloat((Math.random() * 0.4).toFixed(4)),
        closeness_centrality: parseFloat((Math.random() * 0.4).toFixed(4)),
        is_gateway: Math.random() > 0.8
      });
    }
  }

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const curr = r * cols + c;
      if (c + 1 < cols) {
        edges.push({
          source: curr,
          target: curr + 1,
          length_meters: 150.0,
          confidence: parseFloat((0.9 + Math.random() * 0.1).toFixed(2)),
          is_healing_edge: Math.random() > 0.85
        });
      }
      if (r + 1 < rows) {
        edges.push({
          source: curr,
          target: curr + cols,
          length_meters: 150.0,
          confidence: parseFloat((0.9 + Math.random() * 0.1).toFixed(2)),
          is_healing_edge: Math.random() > 0.85
        });
      }
    }
  }

  nodes.forEach(n => {
    n.degree = edges.filter(e => e.source === n.id || e.target === n.id).length;
  });

  return { nodes, edges };
}

// Calculate Largest Connected Component (LCC) size via BFS
function calculateLccSize(nodes: any[], edges: any[], disabledNodes: number[]): number {
  const disabledSet = new Set(disabledNodes);
  const activeNodes = new Set<number>(nodes.map(n => n.id).filter(id => !disabledSet.has(id)));
  const adj: { [key: number]: number[] } = {};
  
  activeNodes.forEach(id => {
    adj[id] = [];
  });
  
  for (const edge of edges) {
    if (activeNodes.has(edge.source) && activeNodes.has(edge.target)) {
      adj[edge.source].push(edge.target);
      adj[edge.target].push(edge.source);
    }
  }

  const visited = new Set<number>();
  let maxLcc = 0;

  activeNodes.forEach(id => {
    if (!visited.has(id)) {
      let size = 0;
      const queue = [id];
      visited.add(id);
      
      while (queue.length > 0) {
        const curr = queue.shift()!;
        size++;
        for (const neighbor of adj[curr] || []) {
          if (!visited.has(neighbor)) {
            visited.add(neighbor);
            queue.push(neighbor);
          }
        }
      }
      
      if (size > maxLcc) {
        maxLcc = size;
      }
    }
  });

  return maxLcc;
}

// Dijkstra routing algorithm
function dijkstra(nodes: any[], edges: any[], source: number, target: number, disabledNodes: number[], disabledEdges: string[], congestion: { [key: string]: number }): { path: number[]; distance: number } {
  const disabledNodeSet = new Set(disabledNodes);
  const disabledEdgeSet = new Set(disabledEdges);

  const adj: { [key: number]: { node: number; weight: number }[] } = {};
  for (const node of nodes) {
    adj[node.id] = [];
  }

  for (const edge of edges) {
    const u = edge.source;
    const v = edge.target;
    const edgeKey1 = `${u}-${v}`;
    const edgeKey2 = `${v}-${u}`;

    if (disabledNodeSet.has(u) || disabledNodeSet.has(v)) continue;
    if (disabledEdgeSet.has(edgeKey1) || disabledEdgeSet.has(edgeKey2)) continue;

    const multiplier = congestion[edgeKey1] || congestion[edgeKey2] || 1.0;
    const weight = edge.length_meters * multiplier;

    adj[u].push({ node: v, weight });
    adj[v].push({ node: u, weight });
  }

  const dist: { [key: number]: number } = {};
  const prev: { [key: number]: number | null } = {};
  const queue = new Set<number>();

  for (const node of nodes) {
    dist[node.id] = Infinity;
    prev[node.id] = null;
    queue.add(node.id);
  }

  dist[source] = 0;

  while (queue.size > 0) {
    let minNode: number | null = null;
    let minDist = Infinity;

    queue.forEach(id => {
      if (dist[id] < minDist) {
        minDist = dist[id];
        minNode = id;
      }
    });

    if (minNode === null || minNode === target || minDist === Infinity) {
      break;
    }

    queue.delete(minNode);

    for (const edge of adj[minNode] || []) {
      if (!queue.has(edge.node)) continue;
      const alt = dist[minNode] + edge.weight;
      if (alt < dist[edge.node]) {
        dist[edge.node] = alt;
        prev[edge.node] = minNode;
      }
    }
  }

  const path: number[] = [];
  let curr: number | null = target;
  while (curr !== null) {
    path.unshift(curr);
    curr = prev[curr];
  }

  if (path[0] !== source) {
    return { path: [], distance: 0 };
  }

  return { path, distance: dist[target] };
}

// Seeded static database
const blr = generateMockNetwork(77.45, 12.90, 77.55, 13.00);
const del = generateMockNetwork(77.10, 28.55, 77.20, 28.65);
const bom = generateMockNetwork(72.80, 18.95, 72.90, 19.05);
const nyc = generateMockNetwork(-74.02, 40.70, -73.92, 40.80);
const tyo = generateMockNetwork(139.70, 35.65, 139.80, 35.75);

const seedCities = [
  {
    _id: 'bengaluru',
    id: 'bengaluru',
    name: 'Bengaluru',
    state: 'Karnataka',
    country: 'India',
    population: 12000000,
    area_sqkm: 741.0,
    zoom_level: 12,
    satellite_source: 'Cartosat-3',
    resolution_m: 0.28,
    total_nodes: blr.nodes.length,
    total_edges: blr.edges.length,
    avg_centrality: 0.124,
    network_resilience_index: 0.854,
    nodes: blr.nodes,
    edges: blr.edges
  },
  {
    _id: 'delhi',
    id: 'delhi',
    name: 'Delhi',
    state: 'Delhi',
    country: 'India',
    population: 31000000,
    area_sqkm: 1484.0,
    zoom_level: 11,
    satellite_source: 'Sentinel-2',
    resolution_m: 10.0,
    total_nodes: del.nodes.length,
    total_edges: del.edges.length,
    avg_centrality: 0.108,
    network_resilience_index: 0.812,
    nodes: del.nodes,
    edges: del.edges
  },
  {
    _id: 'mumbai',
    id: 'mumbai',
    name: 'Mumbai',
    state: 'Maharashtra',
    country: 'India',
    population: 21000000,
    area_sqkm: 603.4,
    zoom_level: 12,
    satellite_source: 'Cartosat-3',
    resolution_m: 0.28,
    total_nodes: bom.nodes.length,
    total_edges: bom.edges.length,
    avg_centrality: 0.135,
    network_resilience_index: 0.785,
    nodes: bom.nodes,
    edges: bom.edges
  },
  {
    _id: 'newyork',
    id: 'newyork',
    name: 'New York',
    state: 'New York',
    country: 'United States',
    population: 8300000,
    area_sqkm: 783.8,
    zoom_level: 12,
    satellite_source: 'Landsat-9',
    resolution_m: 15.0,
    total_nodes: nyc.nodes.length,
    total_edges: nyc.edges.length,
    avg_centrality: 0.158,
    network_resilience_index: 0.912,
    nodes: nyc.nodes,
    edges: nyc.edges
  },
  {
    _id: 'tokyo',
    id: 'tokyo',
    name: 'Tokyo',
    state: 'Tokyo',
    country: 'Japan',
    population: 14000000,
    area_sqkm: 2194.0,
    zoom_level: 12,
    satellite_source: 'ALOS-3',
    resolution_m: 0.8,
    total_nodes: tyo.nodes.length,
    total_edges: tyo.edges.length,
    avg_centrality: 0.115,
    network_resilience_index: 0.884,
    nodes: tyo.nodes,
    edges: tyo.edges
  }
];

// In-memory runtime database for custom dynamic cities
let dynamicCities: any[] = [];

// Stable deterministic traffic cache per run
const trafficCache: { [cityId: string]: any } = {};

function getOrGenerateTraffic(cityId: string, edges: any[]) {
  const normId = cityId.toLowerCase();
  if (trafficCache[normId]) {
    return trafficCache[normId];
  }

  const congestion: { [edgeKey: string]: { level: 'heavy' | 'moderate' | 'clear', multiplier: number } } = {};
  const incidents: any[] = [];

  edges.forEach((edge, idx) => {
    const edgeKey = `${edge.source}-${edge.target}`;
    if (idx % 12 === 0) {
      congestion[edgeKey] = { level: 'heavy', multiplier: 3.0 };
    } else if (idx % 7 === 0) {
      congestion[edgeKey] = { level: 'moderate', multiplier: 1.5 };
    } else {
      congestion[edgeKey] = { level: 'clear', multiplier: 1.0 };
    }

    if (idx % 35 === 0) {
      incidents.push({
        id: `incident-${normId}-${idx}`,
        type: 'closure',
        edge: [edge.source, edge.target],
        description: 'Monsoon Flooding & Waterlogging',
        severity: 'high',
        location: {
          latitude: edge.is_healing_edge ? 12.95 : (12.9 + (idx % 100) * 0.001),
          longitude: edge.is_healing_edge ? 77.52 : (77.45 + (idx % 100) * 0.001)
        }
      });
    } else if (idx % 23 === 0) {
      incidents.push({
        id: `incident-${normId}-${idx}`,
        type: 'construction',
        edge: [edge.source, edge.target],
        description: 'Metro Line Construction',
        severity: 'medium',
        location: {
          latitude: 12.92 + (idx % 100) * 0.0008,
          longitude: 77.47 + (idx % 100) * 0.0008
        }
      });
    }
  });

  const state = { congestion, incidents };
  trafficCache[normId] = state;
  return state;
}

// Master catch-all router
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,DELETE,PATCH,POST,PUT,OPTIONS');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
  );

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { path } = req.query;
  const pathArr = Array.isArray(path) ? path : [path || ''];
  const fullPath = pathArr.join('/');

  try {
    // -------------------------------------------------------------
    // GET /cities
    // -------------------------------------------------------------
    if (req.method === 'GET' && fullPath === 'cities') {
      const allCities = [...seedCities, ...dynamicCities].map(c => ({
        id: c.id,
        name: c.name,
        state: c.state,
        country: c.country,
        population: c.population,
        area_sqkm: c.area_sqkm,
        satellite_source: c.satellite_source,
        resolution_m: c.resolution_m,
        total_nodes: c.total_nodes,
        total_edges: c.total_edges,
        avg_centrality: c.avg_centrality,
        network_resilience_index: c.network_resilience_index
      }));
      return res.status(200).json(allCities);
    }

    // -------------------------------------------------------------
    // POST /cities/osm (Register dynamic OSM city)
    // -------------------------------------------------------------
    if (req.method === 'POST' && fullPath === 'cities/osm') {
      const { city_name, bbox } = req.body;
      if (!city_name || !bbox || !Array.isArray(bbox) || bbox.length !== 4) {
        return res.status(400).json({ error: 'city_name and bbox (4 floats) are required.' });
      }

      const [minLat, minLng, maxLat, maxLng] = bbox.map(Number);
      let nodes: any[] = [];
      let edges: any[] = [];
      let extractedRealOSM = false;

      try {
        const query = `[out:json][timeout:35];(way["highway"](${minLat},${minLng},${maxLat},${maxLng}););out geom;`;
        console.log(`Querying Overpass for ${city_name}...`);
        const overpassRes = await axios.post(
          'https://overpass-api.de/api/interpreter',
          `data=${encodeURIComponent(query)}`,
          {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            timeout: 25000 // 25s limit
          }
        );

        if (overpassRes.data && overpassRes.data.elements && overpassRes.data.elements.length > 0) {
          const network = overpassToNetwork(overpassRes.data.elements);
          nodes = network.nodes;
          edges = network.edges;
          extractedRealOSM = nodes.length > 0;
        }
      } catch (err: any) {
        console.warn(`Overpass download failed for ${city_name}, falling back to synthetic.`, err.message);
      }

      if (!extractedRealOSM) {
        const network = generateFallbackNetwork([minLat, minLng, maxLat, maxLng]);
        nodes = network.nodes;
        edges = network.edges;
      }

      const newCity = {
        _id: city_name.toLowerCase().replace(/[^a-z0-9]/g, '-'),
        id: city_name.toLowerCase().replace(/[^a-z0-9]/g, '-'),
        name: city_name,
        state: 'Global Region',
        country: 'Global',
        population: 500000,
        area_sqkm: 50.0,
        zoom_level: 13,
        satellite_source: extractedRealOSM ? 'OSM Real-time' : 'OSM Resilient Fallback',
        resolution_m: 1.0,
        total_nodes: nodes.length,
        total_edges: edges.length,
        avg_centrality: 0.12,
        network_resilience_index: parseFloat((0.7 + Math.random() * 0.2).toFixed(3)),
        nodes,
        edges
      };

      // Push to in-memory db if not already present
      const existIdx = dynamicCities.findIndex(c => c.id === newCity.id || c.name.toLowerCase() === newCity.name.toLowerCase());
      if (existIdx >= 0) {
        dynamicCities[existIdx] = newCity;
      } else {
        dynamicCities.push(newCity);
      }

      return res.status(200).json(newCity);
    }

    // -------------------------------------------------------------
    // GET /cities/:cityId
    // -------------------------------------------------------------
    if (req.method === 'GET' && fullPath.startsWith('cities/')) {
      const cityId = pathArr[1];
      const city = [...seedCities, ...dynamicCities].find(
        c => c.id === cityId || c.name.toLowerCase() === cityId.toLowerCase()
      );
      if (!city) {
        return res.status(404).json({ error: 'City not found' });
      }
      return res.status(200).json(city);
    }

    // -------------------------------------------------------------
    // POST /simulations/:cityId/stress-test
    // -------------------------------------------------------------
    if (req.method === 'POST' && fullPath.includes('stress-test')) {
      const cityId = pathArr[1];
      const { scenario_type, flood_bounds, ablate_nodes } = req.body;
      const city = [...seedCities, ...dynamicCities].find(
        c => c.id === cityId || c.name.toLowerCase() === cityId.toLowerCase()
      );
      if (!city) {
        return res.status(404).json({ error: 'City not found' });
      }

      const disabled: number[] = [];
      if (scenario_type === 'flood' && flood_bounds) {
        const [minX, minY, maxX, maxY] = flood_bounds.map(Number);
        city.nodes.forEach((n: any) => {
          if (minX <= n.longitude && n.longitude <= maxX && minY <= n.latitude && n.latitude <= maxY) {
            disabled.push(n.id);
          }
        });
      } else if (ablate_nodes) {
        disabled.push(...ablate_nodes.map(Number));
      }

      const baselineLcc = city.total_nodes;
      const perturbedLcc = calculateLccSize(city.nodes, city.edges, disabled);
      const lossPercent = parseFloat((((baselineLcc - perturbedLcc) / baselineLcc) * 100).toFixed(2));
      const resilienceIndex = parseFloat((Math.max(0, 1 - (lossPercent / 100)) * city.network_resilience_index).toFixed(3));

      return res.status(200).json({
        scenario_type,
        removed_node_count: disabled.length,
        baseline_lcc_size: baselineLcc,
        perturbed_lcc_size: perturbedLcc,
        lcc_loss_percent: lossPercent,
        resilience_index: resilienceIndex,
        critical: resilienceIndex < 0.65,
        recommendation_text: resilienceIndex < 0.65 
          ? "CRITICAL RISK — Large component disconnect detected. Introduce redundant connectors immediately." 
          : "STABLE — Component connectivity remains robust. Monitor critical bridges."
      });
    }

    // -------------------------------------------------------------
    // POST /simulations/:cityId/route
    // -------------------------------------------------------------
    if (req.method === 'POST' && fullPath.includes('route')) {
      const cityId = pathArr[1];
      const { source_node, target_node, disabled_nodes, disabled_edges } = req.body;
      const city = [...seedCities, ...dynamicCities].find(
        c => c.id === cityId || c.name.toLowerCase() === cityId.toLowerCase()
      );
      if (!city) {
        return res.status(404).json({ error: 'City not found' });
      }

      const traffic = getOrGenerateTraffic(cityId, city.edges || []);
      const congestionMults: { [key: string]: number } = {};
      Object.entries(traffic.congestion).forEach(([k, v]: any) => {
        congestionMults[k] = v.multiplier;
      });

      const finalDisabledEdges = [...(disabled_edges || [])];
      traffic.incidents.forEach((inc: any) => {
        if (inc.type === 'closure') {
          finalDisabledEdges.push(`${inc.edge[0]}-${inc.edge[1]}`);
        }
      });

      // Compute shortest path via Dijkstra
      const routeRes = dijkstra(
        city.nodes,
        city.edges,
        Number(source_node),
        Number(target_node),
        disabled_nodes ? disabled_nodes.map(Number) : [],
        finalDisabledEdges,
        congestionMults
      );

      // Compute alternative path by temporarily blocking the shortest path nodes
      let altRoute = { path: [] as number[], distance: 0 };
      if (routeRes.path.length > 2) {
        const intermediateNodes = routeRes.path.slice(1, -1);
        altRoute = dijkstra(
          city.nodes,
          city.edges,
          Number(source_node),
          Number(target_node),
          [...(disabled_nodes || []).map(Number), ...intermediateNodes],
          finalDisabledEdges,
          congestionMults
        );
      }

      return res.status(200).json({
        shortest_path: routeRes.path,
        distance_meters: parseFloat(routeRes.distance.toFixed(2)),
        alternative_path: altRoute.path,
        alternative_distance_meters: parseFloat(altRoute.distance.toFixed(2))
      });
    }

    // -------------------------------------------------------------
    // GET /simulations/feed/disasters
    // -------------------------------------------------------------
    if (req.method === 'GET' && fullPath === 'simulations/feed/disasters') {
      return res.status(200).json([
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
    }

    // -------------------------------------------------------------
    // POST /simulations/feed/copilot
    // -------------------------------------------------------------
    if (req.method === 'POST' && fullPath === 'simulations/feed/copilot') {
      const { query } = req.body;
      const q = (query || '').toLowerCase();
      let reply = "";

      if (q.includes("bridge") || q.includes("fail") || q.includes("ablate") || q.includes("remove")) {
        reply = "Simulating structural ablate failure. Disabling the primary connecting corridor drops the global Resilience Index to 72.4%. It is recommended to designate Node 25 as a secondary transit corridor and reinforce the parallel grid bridges within 500 meters to prevent complete ward isolation.";
      } else if (q.includes("critical") || q.includes("bottleneck") || q.includes("junction")) {
        reply = "RouteGuard AI graph analysis identifies that outer ring roads and central junctions exhibit the highest Betweenness Centrality scores. These nodes act as 'gatekeeper' intersections; their failure causes cascading traffic gridlock on all surrounding arterial streets.";
      } else if (q.includes("safe") || q.includes("evacuate") || q.includes("flood")) {
        reply = "Emergency evacuation corridor computed. The primary shortest path avoids the active GDACS flood zone at Bellandur. The route covers 450 meters with an estimated arrival time of 8 minutes for emergency vehicles, using our dynamic traffic friction weights.";
      } else {
        reply = "RouteGuard AI Copilot active. You can ask me to simulate bridge collapses, identify the most critical bottleneck intersections, or calculate safe evacuation routes avoiding GDACS flood boundaries.";
      }

      return res.status(200).json({
        query,
        reply,
        timestamp: new Date().toISOString()
      });
    }

    // -------------------------------------------------------------
    // GET /traffic/:cityId/congestion
    // -------------------------------------------------------------
    if (req.method === 'GET' && fullPath.includes('congestion')) {
      const cityId = pathArr[1];
      const city = [...seedCities, ...dynamicCities].find(
        c => c.id === cityId || c.name.toLowerCase() === cityId.toLowerCase()
      );
      if (!city) {
        return res.status(404).json({ error: 'City not found' });
      }

      const trafficState = getOrGenerateTraffic(cityId, city.edges || []);
      return res.status(200).json(trafficState);
    }

    // Endpoint not matched
    return res.status(404).json({ error: `Not Found: ${req.method} ${fullPath}` });

  } catch (error: any) {
    console.error(`API Error on ${req.method} ${fullPath}:`, error);
    return res.status(500).json({ error: error.message || 'Internal Server Error' });
  }
}
