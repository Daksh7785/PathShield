import { Request, Response, NextFunction } from 'express';
import rateLimit from 'express-rate-limit';

// Mock Redis connection / Local cache store
const localCache = new Map<string, { data: any; expiry: number }>();

export const gatewayCache = (ttlSeconds: number) => {
  return (req: Request, res: Response, next: NextFunction) => {
    if (req.method !== 'GET') return next();
    
    const key = req.originalUrl;
    const cached = localCache.get(key);
    
    if (cached && cached.expiry > Date.now()) {
      return res.json(cached.data);
    }
    
    // Override res.json to capture response data
    const originalJson = res.json;
    res.json = function (body: any) {
      localCache.set(key, {
        data: body,
        expiry: Date.now() + (ttlSeconds * 1000)
      });
      return originalJson.call(this, body);
    };
    
    next();
  };
};

// API Key Validation Middleware
const VALID_API_KEYS = new Set(['rg_live_9948ff72', 'rg_test_b874fa11']);

export const validateApiKey = (req: Request, res: Response, next: NextFunction) => {
  const apiKey = req.headers['x-api-key'] || req.query.apiKey;
  
  if (!apiKey || !VALID_API_KEYS.has(apiKey as string)) {
    return res.status(401).json({
      error: 'Unauthorized',
      message: 'Invalid or missing API key (use x-api-key header).'
    });
  }
  next();
};

// JWT Token Verification Middleware
export const validateJwt = (req: Request, res: Response, next: NextFunction) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      error: 'Unauthorized',
      message: 'Missing or malformed Authorization Bearer token.'
    });
  }
  
  const token = authHeader.split(' ')[1];
  if (token !== 'routeguard_valid_jwt_token') {
    return res.status(403).json({
      error: 'Forbidden',
      message: 'Invalid JWT Token.'
    });
  }
  
  next();
};

// Request logging audit middleware
export const requestLogger = (req: Request, res: Response, next: NextFunction) => {
  const startTime = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    console.log(`[GATEWAY LOG] ${new Date().toISOString()} | ${req.method} ${req.originalUrl} | Status: ${res.statusCode} | ${duration}ms | IP: ${req.ip}`);
  });
  next();
};

// Rate Limiter
export const gatewayLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per window
  message: {
    error: 'Too Many Requests',
    message: 'Rate limit exceeded on RouteGuard gateway. Please retry in 15 minutes.'
  }
});
