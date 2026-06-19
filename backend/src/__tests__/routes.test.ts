import simulationsRouter from '../routes/simulations';
import trafficRouter from '../routes/traffic';
import { Request, Response } from 'express';
import { setDbMock } from '../config/db';

beforeAll(() => {
  setDbMock(true);
});

// Helper to mock express Response
const mockResponse = () => {
  const res = {} as Response;
  res.status = jest.fn().mockReturnValue(res);
  res.json = jest.fn().mockReturnValue(res);
  return res;
};

const dummyNext = () => {};

describe('Simulations API Endpoint Router Tests', () => {
  it('should return mock disasters feed with correct structure', () => {
    const req = { method: 'GET', url: '/feed/disasters' } as Request;
    const res = mockResponse();
    
    const disastersRoute = (simulationsRouter.stack as any[]).find(
      layer => layer.route && layer.route.path === '/feed/disasters' && layer.route.methods.get
    );
    
    expect(disastersRoute).toBeDefined();
    const handler = disastersRoute.route.stack[0].handle;
    
    handler(req, res, dummyNext);
    expect(res.json).toHaveBeenCalled();
    const mockData = (res.json as jest.Mock).mock.calls[0][0];
    expect(Array.isArray(mockData)).toBe(true);
    expect(mockData.length).toBeGreaterThan(0);
    expect(mockData[0]).toHaveProperty('id');
    expect(mockData[0]).toHaveProperty('type');
    expect(mockData[0]).toHaveProperty('severity');
  });

  it('should reply with structural ablate failure details on bridge fails query', async () => {
    const req = {
      method: 'POST',
      url: '/feed/copilot',
      body: { query: 'What happens if a bridge fails in Bengaluru?' }
    } as unknown as Request;
    const res = mockResponse();
    
    const copilotRoute = (simulationsRouter.stack as any[]).find(
      layer => layer.route && layer.route.path === '/feed/copilot' && layer.route.methods.post
    );
    
    expect(copilotRoute).toBeDefined();
    const handler = copilotRoute.route.stack[0].handle;
    
    await handler(req, res, dummyNext);
    expect(res.json).toHaveBeenCalled();
    const replyObj = (res.json as jest.Mock).mock.calls[0][0];
    expect(replyObj.reply).toContain('Simulating structural ablate failure');
  });
});

describe('Traffic API Endpoint Router Tests', () => {
  it('should return mock traffic details for a seeded city', async () => {
    const req = {
      method: 'GET',
      url: '/bengaluru/congestion',
      params: { cityId: 'bengaluru' }
    } as unknown as Request;
    const res = mockResponse();
    
    const congestionRoute = (trafficRouter.stack as any[]).find(
      layer => layer.route && layer.route.path === '/:cityId/congestion' && layer.route.methods.get
    );
    
    expect(congestionRoute).toBeDefined();
    const handler = congestionRoute.route.stack[0].handle;
    
    await handler(req, res, dummyNext);
    expect(res.json).toHaveBeenCalled();
    const trafficData = (res.json as jest.Mock).mock.calls[0][0];
    expect(trafficData).toHaveProperty('congestion');
    expect(trafficData).toHaveProperty('incidents');
    expect(Array.isArray(trafficData.incidents)).toBe(true);
  });
});
