import React, { useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, useMap, Circle } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix default marker icon issue in Leaflet + Next.js
useEffect; // Dummy reference to prevent unused warning

interface MapNode {
  id: number;
  longitude: number;
  latitude: number;
  degree: number;
  node_type: string;
  betweenness_centrality: number;
  closeness_centrality: number;
  is_gateway: boolean;
}

interface MapEdge {
  source: number;
  target: number;
  length_meters: number;
  confidence: number;
  is_healing_edge: boolean;
}

interface MapComponentProps {
  center: [number, number];
  zoom: number;
  nodes: MapNode[];
  edges: MapEdge[];
  shortestPath?: number[];
  alternativePath?: number[];
  disabledNodes?: number[];
  heatmapType?: 'centrality' | 'confidence' | null;
  onNodeClick?: (nodeId: number) => void;
  disasters?: any[];
  congestion?: { [edgeKey: string]: { level: 'heavy' | 'moderate' | 'clear', multiplier: number } };
}

// Sub-component to fly to city center when center changes
function ChangeView({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, zoom);
  }, [center, zoom, map]);
  return null;
}

export default function MapComponent({
  center,
  zoom,
  nodes = [],
  edges = [],
  shortestPath = [],
  alternativePath = [],
  disabledNodes = [],
  heatmapType = null,
  onNodeClick,
  disasters = [],
  congestion = {}
}: MapComponentProps) {
  
  // Find node coordinates helper
  const getNodeCoords = (nodeId: number): [number, number] | null => {
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return null;
    return [node.latitude, node.longitude];
  };

  // Get color for edges
  const getEdgeColor = (edge: MapEdge) => {
    if (edge.is_healing_edge) return '#10b981'; // Green for healed edges
    
    // Check congestion levels
    const key = `${edge.source}-${edge.target}`;
    const revKey = `${edge.target}-${edge.source}`;
    const cong = congestion[key] || congestion[revKey];
    
    if (cong) {
      if (cong.level === 'heavy') return '#ef4444'; // Red
      if (cong.level === 'moderate') return '#f97316'; // Orange
    }
    
    return '#4b5563'; // Grey for standard roads
  };

  // Get weight for edges
  const getEdgeWeight = (edge: MapEdge) => {
    if (edge.is_healing_edge) return 3.5;
    
    const key = `${edge.source}-${edge.target}`;
    const revKey = `${edge.target}-${edge.source}`;
    const cong = congestion[key] || congestion[revKey];
    
    if (cong && cong.level !== 'clear') return 4.5;
    return 2.5;
  };

  // Node styles
  const getNodeColor = (node: MapNode) => {
    if (disabledNodes.includes(node.id)) return '#ef4444'; // Red if disabled
    
    if (heatmapType === 'centrality') {
      const bc = node.betweenness_centrality;
      if (bc > 0.4) return '#f43f5e'; // High Centrality - Red
      if (bc > 0.2) return '#fb923c'; // Medium Centrality - Orange
      return '#3b82f6'; // Low Centrality - Blue
    }
    
    if (node.is_gateway) return '#fbbf24'; // Yellow for gateways
    return '#6366f1'; // Violet/Indigo for normal nodes
  };

  // Extract polyline geometries for shortest path
  const shortestPathCoords = shortestPath
    .map(id => getNodeCoords(id))
    .filter((coords): coords is [number, number] => coords !== null);

  // Extract polyline geometries for alternative path
  const alternativePathCoords = alternativePath
    .map(id => getNodeCoords(id))
    .filter((coords): coords is [number, number] => coords !== null);

  return (
    <div className="w-full h-full relative rounded-2xl overflow-hidden border border-slate-800">
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <ChangeView center={center} zoom={zoom} />
        
        {/* Dark map tiles */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* Render standard and healed edges */}
        {edges.map((edge, idx) => {
          const srcNode = nodes.find(n => n.id === edge.source);
          const tgtNode = nodes.find(n => n.id === edge.target);
          if (!srcNode || !tgtNode) return null;
          
          return (
            <Polyline
              key={`edge-${idx}`}
              positions={[
                [srcNode.latitude, srcNode.longitude],
                [tgtNode.latitude, tgtNode.longitude]
              ]}
              pathOptions={{
                color: getEdgeColor(edge),
                weight: getEdgeWeight(edge),
                opacity: edge.is_healing_edge ? 0.9 : 0.6,
                dashArray: edge.is_healing_edge ? '6,6' : undefined
              }}
            >
              <Popup>
                <div className="text-xs text-slate-800 font-sans">
                  <p className="font-semibold">{edge.is_healing_edge ? 'Healed Topological Link' : 'Existing Road Edge'}</p>
                  <p>Source Node: {edge.source}</p>
                  <p>Target Node: {edge.target}</p>
                  <p>Length: {edge.length_meters.toFixed(1)} meters</p>
                  <p>Confidence: {(edge.confidence * 100).toFixed(0)}%</p>
                </div>
              </Popup>
            </Polyline>
          );
        })}

        {/* Render disaster hazard regions */}
        {disasters.map((disaster, idx) => (
          <React.Fragment key={`disaster-layer-${idx}`}>
            <Circle
              center={[disaster.latitude, disaster.longitude]}
              radius={disaster.radius_meters || 500}
              pathOptions={{
                color: disaster.severity === 'high' ? '#ef4444' : '#f97316',
                fillColor: disaster.severity === 'high' ? '#ef4444' : '#f97316',
                fillOpacity: 0.12,
                weight: 1.5,
                dashArray: '5, 5'
              }}
            />
            <CircleMarker
              center={[disaster.latitude, disaster.longitude]}
              radius={10}
              pathOptions={{
                fillColor: disaster.type === 'flood' ? '#3b82f6' : '#ef4444',
                fillOpacity: 0.95,
                color: '#ffffff',
                weight: 2
              }}
            >
              <Popup>
                <div className="text-xs text-slate-800 font-sans p-1">
                  <h4 className="font-bold border-b pb-1 mb-1 text-slate-900">{disaster.title}</h4>
                  <p>Type: <span className="uppercase font-semibold">{disaster.type}</span></p>
                  <p>Severity: <span className="uppercase text-red-600 font-bold">{disaster.severity}</span></p>
                  <p>Affected Area Radius: {disaster.radius_meters}m</p>
                </div>
              </Popup>
            </CircleMarker>
          </React.Fragment>
        ))}

        {/* Render shortest path overlay */}
        {shortestPathCoords.length > 1 && (
          <Polyline
            positions={shortestPathCoords}
            pathOptions={{
              color: '#3b82f6', // Bright Blue
              weight: 5,
              opacity: 0.95
            }}
          />
        )}

        {/* Render alternative path overlay */}
        {alternativePathCoords.length > 1 && (
          <Polyline
            positions={alternativePathCoords}
            pathOptions={{
              color: '#10b981', // Bright Green
              weight: 5,
              opacity: 0.95,
              dashArray: '3, 6'
            }}
          />
        )}

        {/* Render nodes */}
        {nodes.map((node, idx) => (
          <CircleMarker
            key={`node-${node.id}`}
            center={[node.latitude, node.longitude]}
            radius={node.is_gateway ? 6 : 4}
            pathOptions={{
              fillColor: getNodeColor(node),
              fillOpacity: 0.85,
              color: '#0a0b10',
              weight: 1.5
            }}
            eventHandlers={{
              click: () => {
                if (onNodeClick) onNodeClick(node.id);
              }
            }}
          >
            <Popup>
              <div className="text-xs text-slate-800 font-sans">
                <p className="font-semibold">Node ID: {node.id}</p>
                <p>Type: {node.node_type}</p>
                <p>Degree (Valency): {node.degree}</p>
                <p>Betweenness Centrality: {node.betweenness_centrality.toFixed(4)}</p>
                <p>Gateway Intersection: {node.is_gateway ? 'YES' : 'NO'}</p>
                <p>Coordinates: {node.latitude.toFixed(5)}, {node.longitude.toFixed(5)}</p>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
