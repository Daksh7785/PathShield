import { Router, Request, Response } from 'express';
import { isDbMock, MockDB } from '../config/db';
import { City } from '../models/City';

const router = Router();

// Session cache to keep traffic consistent for a given run
export const trafficCache: { [cityId: string]: any } = {};

export function getOrGenerateTraffic(cityId: string, edges: any[]) {
  const normId = cityId.toLowerCase();
  if (trafficCache[normId]) {
    return trafficCache[normId];
  }

  const congestion: { [edgeKey: string]: { level: 'heavy' | 'moderate' | 'clear', multiplier: number } } = {};
  const incidents: any[] = [];

  // Generate traffic features deterministically per edge index to keep it stable
  edges.forEach((edge, idx) => {
    const edgeKey = `${edge.source}-${edge.target}`;
    
    // ~8% heavy traffic zones
    if (idx % 12 === 0) {
      congestion[edgeKey] = { level: 'heavy', multiplier: 3.0 };
    }
    // ~15% moderate traffic zones
    else if (idx % 7 === 0) {
      congestion[edgeKey] = { level: 'moderate', multiplier: 1.5 };
    } else {
      congestion[edgeKey] = { level: 'clear', multiplier: 1.0 };
    }

    // ~3% waterlogging/closure incidents
    if (idx % 35 === 0) {
      incidents.push({
        id: `incident-${normId}-${idx}`,
        type: 'closure',
        edge: [edge.source, edge.target],
        description: 'Monsoon Flooding & Waterlogging',
        severity: 'high',
        location: {
          latitude: edge.is_healing_edge ? 12.95 : (12.9 + (idx % 100) * 0.001), // Approximate coords
          longitude: edge.is_healing_edge ? 77.52 : (77.45 + (idx % 100) * 0.001)
        }
      });
    }
    // ~5% metro/construction narrowing lanes
    else if (idx % 23 === 0) {
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

router.get('/:cityId/congestion', async (req: Request, res: Response) => {
  const { cityId } = req.params;
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

    const trafficState = getOrGenerateTraffic(cityId, city.edges || []);
    return res.json(trafficState);
  } catch (error: any) {
    return res.status(500).json({ error: error.message });
  }
});

export default router;
