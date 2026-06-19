import mongoose from 'mongoose';

export let isDbMock = false;

export function setDbMock(val: boolean) {
  isDbMock = val;
  if (val) {
    _initializeMockDB();
  }
}

// Mock database store
let mockCities: any[] = [];

export async function connectDB() {
  const mongoURI = process.env.MONGO_URI || 'mongodb://localhost:27017/routeresilience';
  
  console.log(`Connecting to MongoDB at: ${mongoURI}`);
  try {
    mongoose.set('strictQuery', true);
    await mongoose.connect(mongoURI, {
      serverSelectionTimeoutMS: 2000
    });
    console.log('✓ MongoDB Connected Successfully.');
    isDbMock = false;
  } catch (error: any) {
    console.warn(`⚠️ MongoDB connection failed: ${error.message}. Activating in-memory DB fallback.`);
    isDbMock = true;
    _initializeMockDB();
  }
}

function generateMockNetwork(minx: number, miny: number, maxx: number, maxy: number) {
  const nodes: any[] = [];
  const edges: any[] = [];
  const cols = 10;
  const rows = 10;
  
  const x_coords = Array.from({length: cols}, (_, i) => minx + (i * (maxx - minx)) / (cols - 1));
  const y_coords = Array.from({length: rows}, (_, i) => miny + (i * (maxy - miny)) / (rows - 1));
  
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
        betweenness_centrality: Math.random() * 0.4,
        closeness_centrality: Math.random() * 0.4,
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
          confidence: 0.9 + Math.random() * 0.1,
          is_healing_edge: Math.random() > 0.85
        });
      }
      if (r + 1 < rows) {
        edges.push({
          source: curr,
          target: curr + cols,
          length_meters: 150.0,
          confidence: 0.9 + Math.random() * 0.1,
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

function _initializeMockDB() {
  const blr = generateMockNetwork(77.45, 12.90, 77.55, 13.00);
  const del = generateMockNetwork(77.10, 28.55, 77.20, 28.65);
  const bom = generateMockNetwork(72.80, 18.95, 72.90, 19.05);
  const nyc = generateMockNetwork(-74.02, 40.70, -73.92, 40.80);
  const tyo = generateMockNetwork(139.70, 35.65, 139.80, 35.75);
  
  mockCities = [
    {
      _id: 'bengaluru-id',
      id: 'bengaluru-id',
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
      _id: 'delhi-id',
      id: 'delhi-id',
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
      _id: 'mumbai-id',
      id: 'mumbai-id',
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
      _id: 'newyork-id',
      id: 'newyork-id',
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
      _id: 'tokyo-id',
      id: 'tokyo-id',
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
  console.log(`✓ Seeded ${mockCities.length} global cities in the mock database.`);
}

export const MockDB = {
  getCities: () => mockCities,
  getCityById: (id: string) => {
    return mockCities.find(c => c._id === id || c.name.toLowerCase() === id.toLowerCase());
  },
  saveCity: (cityData: any) => {
    const idx = mockCities.findIndex(c => c.name.toLowerCase() === cityData.name.toLowerCase());
    if (idx >= 0) {
      mockCities[idx] = { ...mockCities[idx], ...cityData };
      return mockCities[idx];
    } else {
      const newCity = { _id: `${cityData.name.toLowerCase()}-id`, id: `${cityData.name.toLowerCase()}-id`, ...cityData };
      mockCities.push(newCity);
      return newCity;
    }
  }
};
