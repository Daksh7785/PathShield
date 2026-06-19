import { Router, Request, Response } from 'express';
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
