import { Router, Request, Response } from 'express';
import axios from 'axios';
import { City } from '../models/City';
import { isDbMock, MockDB } from '../config/db';

const router = Router();

// List all cities
router.get('/', async (req: Request, res: Response) => {
  try {
    if (isDbMock) {
      const cities = MockDB.getCities();
      return res.json(cities);
    }
    const cities = await City.find({}, '-nodes -edges');
    return res.json(cities);
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

// Create city dynamically via OSM downloader
router.post('/osm', async (req: Request, res: Response) => {
  const { city_name, bbox } = req.body;
  if (!city_name || !bbox || !Array.isArray(bbox) || bbox.length !== 4) {
    return res.status(400).json({ error: 'city_name and bbox (4 floats) are required.' });
  }

  const GIS_ENGINE_URL = process.env.GIS_ENGINE_URL || 'http://localhost:8002';
  try {
    console.log(`Forwarding OSM download/generation for ${city_name} to GIS Engine: ${GIS_ENGINE_URL}/osm`);
    const gisRes = await axios.post(`${GIS_ENGINE_URL}/osm`, {
      city_name,
      bbox
    }, { timeout: 90000 }); // 90-second timeout for Overpass API calls
    
    const rawNodes: any[] = gisRes.data?.nodes || [];
    const rawEdges: any[] = gisRes.data?.edges || [];
    const total_nodes: number = gisRes.data?.total_nodes ?? rawNodes.length;
    const total_edges: number = gisRes.data?.total_edges ?? rawEdges.length;
    
    const newCityData = {
      name: city_name,
      state: 'Global Region',
      country: 'Global',
      population: 500000,
      area_sqkm: 50.0,
      zoom_level: 13,
      satellite_source: 'OSM Vector',
      resolution_m: 1.0,
      total_nodes,
      total_edges,
      avg_centrality: 0.12,
      network_resilience_index: 0.82,
      nodes: rawNodes,
      edges: rawEdges
    };

    if (isDbMock) {
      const savedCity = MockDB.saveCity(newCityData);
      return res.json(savedCity);
    } else {
      const city = new City(newCityData);
      await city.save();
      return res.json(city);
    }
  } catch (error: any) {
    console.error('Failed to create dynamic OSM city:', error.message);
    return res.status(500).json({ error: error.message });
  }
});

// Get city by ID or name
router.get('/:cityId', async (req: Request, res: Response) => {
  const { cityId } = req.params;
  try {
    if (isDbMock) {
      const city = MockDB.getCityById(cityId);
      if (!city) {
        return res.status(404).json({ error: 'City not found' });
      }
      return res.json(city);
    }
    
    // Check if valid ObjectId or query by name
    let city;
    if (cityId.match(/^[0-9a-fA-F]{24}$/)) {
      city = await City.findById(cityId);
    } else {
      city = await City.findOne({ name: new RegExp('^' + cityId + '$', 'i') });
    }
    
    if (!city) {
      return res.status(404).json({ error: 'City not found' });
    }
    return res.json(city);
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

export default router;
