import express from 'express';
import http from 'http';
import { Server } from 'socket.io';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import rateLimit from 'express-rate-limit';

import { connectDB } from './config/db';
import citiesRouter from './routes/cities';
import simulationsRouter from './routes/simulations';
import trafficRouter from './routes/traffic';

dotenv.config();

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

const PORT = process.env.PORT || 8000;

// Global Middlewares
app.use(cors());
app.use(helmet({
  contentSecurityPolicy: false // Relax for development/GIS map assets
}));
app.use(express.json({ limit: '50mb' }));

// Rate Limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000, // Limit each IP to 1000 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});
app.use('/api', limiter);

// API Routes
app.use('/api/v1/cities', citiesRouter);
app.use('/api/v1/simulations', simulationsRouter);
app.use('/api/v1/traffic', trafficRouter);

// Health Check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', version: '1.0.0', service: 'backend-gateway' });
});

// Socket.IO Events
io.on('connection', (socket) => {
  console.log(`Socket client connected: ${socket.id}`);
  
  socket.on('join-simulation', (cityId) => {
    socket.join(cityId);
    console.log(`Socket joined room: ${cityId}`);
  });
  
  socket.on('disconnect', () => {
    console.log(`Socket client disconnected: ${socket.id}`);
  });
});

// Connect to Database and start server
async function startServer() {
  await connectDB();
  
  server.listen(PORT, () => {
    console.log(`╔══════════════════════════════════════════════╗`);
    console.log(`║  PATHSHIELD GATEWAY — RUNNING                ║`);
    console.log(`║  Port: ${PORT}                                  ║`);
    console.log(`║  Environment: ${process.env.NODE_ENV || 'development'}            ║`);
    console.log(`╚══════════════════════════════════════════════╝`);
  });
}

startServer();

export { app, server, io };
