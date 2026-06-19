import { Schema, model, Document } from 'mongoose';

export interface INode {
  id: number;
  longitude: number;
  latitude: number;
  degree: number;
  node_type: string;
  betweenness_centrality: number;
  closeness_centrality: number;
  is_gateway: boolean;
}

export interface IEdge {
  source: number;
  target: number;
  length_meters: number;
  confidence: number;
  is_healing_edge: boolean;
}

export interface ICity extends Document {
  name: string;
  state: string;
  country: string;
  population: number;
  area_sqkm: number;
  zoom_level: number;
  satellite_source: string;
  resolution_m: number;
  total_nodes: number;
  total_edges: number;
  avg_centrality: number;
  network_resilience_index: number;
  nodes: INode[];
  edges: IEdge[];
}

const NodeSchema = new Schema<INode>({
  id: { type: Number, required: true },
  longitude: { type: Number, required: true },
  latitude: { type: Number, required: true },
  degree: { type: Number, default: 0 },
  node_type: { type: String, default: 'intersection' },
  betweenness_centrality: { type: Number, default: 0.0 },
  closeness_centrality: { type: Number, default: 0.0 },
  is_gateway: { type: Boolean, default: false }
});

const EdgeSchema = new Schema<IEdge>({
  source: { type: Number, required: true },
  target: { type: Number, required: true },
  length_meters: { type: Number, default: 0.0 },
  confidence: { type: Number, default: 1.0 },
  is_healing_edge: { type: Boolean, default: false }
});

const CitySchema = new Schema<ICity>({
  name: { type: String, required: true, unique: true },
  state: { type: String, required: true },
  country: { type: String, required: true },
  population: { type: Number, required: true },
  area_sqkm: { type: Number, default: 0.0 },
  zoom_level: { type: Number, default: 12 },
  satellite_source: { type: String, default: 'Sentinel-2' },
  resolution_m: { type: Number, default: 10.0 },
  total_nodes: { type: Number, default: 0 },
  total_edges: { type: Number, default: 0 },
  avg_centrality: { type: Number, default: 0.0 },
  network_resilience_index: { type: Number, default: 1.0 },
  nodes: [NodeSchema],
  edges: [EdgeSchema]
}, { timestamps: true });

export const City = model<ICity>('City', CitySchema);
