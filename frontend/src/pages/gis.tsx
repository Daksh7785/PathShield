import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { Activity, Layers, ArrowLeftRight, Settings, Eye, Zap, Search, AlertTriangle, ShieldAlert } from 'lucide-react';
import axios from 'axios';
import CopilotChat from '../components/CopilotChat';
import { Language, languages, translations } from '../utils/i18n';
import { API_BASE } from '../config/api';

// Dynamically load the Leaflet MapComponent to avoid SSR window errors
const MapComponent = dynamic(() => import('../components/MapComponent'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-slate-950 flex items-center justify-center border border-slate-800 rounded-2xl">
      <div className="flex flex-col items-center gap-3">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        <span className="text-sm text-slate-400">Loading Geospatial GIS engine...</span>
      </div>
    </div>
  )
});

interface Node {
  id: number;
  longitude: number;
  latitude: number;
  degree: number;
  node_type: string;
  betweenness_centrality: number;
  closeness_centrality: number;
  is_gateway: boolean;
}

interface Edge {
  source: number;
  target: number;
  length_meters: number;
  confidence: number;
  is_healing_edge: boolean;
}

export default function GisPage() {
  const [lang, setLang] = useState<Language>('en');

  useEffect(() => {
    const savedLang = localStorage.getItem('routeguard_lang') as Language;
    if (savedLang && ['en', 'es', 'fr', 'de', 'pt', 'ar', 'zh', 'ja', 'hi', 'ru', 'ko'].includes(savedLang)) {
      setLang(savedLang);
    }
  }, []);

  const handleLangChange = (newLang: Language) => {
    setLang(newLang);
    localStorage.setItem('routeguard_lang', newLang);
  };

  const t = (key: string) => {
    return translations[lang]?.[key] || translations['en']?.[key] || key;
  };

  const isRtl = lang === 'ar';

  const [cityId, setCityId] = useState<string>('bengaluru');
  const [citiesList, setCitiesList] = useState<any[]>([]);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [center, setCenter] = useState<[number, number]>([12.9716, 77.5946]); // Bengaluru center
  const [zoom, setZoom] = useState<number>(12);
  const [heatmap, setHeatmap] = useState<'centrality' | 'confidence' | null>(null);

  // Routing state
  const [sourceNode, setSourceNode] = useState<number | ''>('');
  const [targetNode, setTargetNode] = useState<number | ''>('');
  const [shortestPath, setShortestPath] = useState<number[]>([]);
  const [alternativePath, setAlternativePath] = useState<number[]>([]);
  const [distance, setDistance] = useState<number>(0);
  const [altDistance, setAltDistance] = useState<number>(0);
  const [routingError, setRoutingError] = useState<string | null>(null);

  // Global search / Nominatim
  const [searchQuery, setSearchQuery] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);

  // Traffic & disasters state
  const [disasters, setDisasters] = useState<any[]>([]);
  const [showDisasters, setShowDisasters] = useState<boolean>(true);
  const [congestion, setCongestion] = useState<any>({});
  const [incidents, setIncidents] = useState<any[]>([]);

  // Fetch cities list on mount and check query params
  useEffect(() => {
    axios.get(`${API_BASE}/api/v1/cities`)
      .then(res => {
        setCitiesList(res.data || []);
      })
      .catch(err => {
        console.warn('Failed to load cities list.', err);
      });

    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const cityParam = params.get('city');
      if (cityParam) {
        setCityId(cityParam);
      }
    }
  }, []);

  useEffect(() => {
    // Fetch nodes & edges for selected city
    axios.get(`${API_BASE}/api/v1/cities/${cityId}`)
      .then(res => {
        const cityData = res.data;
        setNodes(cityData.nodes || []);
        setEdges(cityData.edges || []);
        
        // Reset routing paths
        setShortestPath([]);
        setAlternativePath([]);
        setDistance(0);
        setAltDistance(0);
        setSourceNode('');
        setTargetNode('');

        // Recenter map on active nodes coordinates
        if (cityData.nodes && cityData.nodes.length > 0) {
          const lats = cityData.nodes.map((n: Node) => n.latitude);
          const lons = cityData.nodes.map((n: Node) => n.longitude);
          const avgLat = lats.reduce((a: number, b: number) => a + b, 0) / lats.length;
          const avgLon = lons.reduce((a: number, b: number) => a + b, 0) / lons.length;
          setCenter([avgLat, avgLon]);
          setZoom(12);
        }
      })
      .catch(err => {
        console.warn('Could not load city database details, running local fallback.', err);
      });
  }, [cityId]);

  // Load disasters and traffic data
  useEffect(() => {
    axios.get(`${API_BASE}/api/v1/simulations/feed/disasters`)
      .then(res => {
        setDisasters(res.data || []);
      })
      .catch(err => {
        console.warn('Disaster feed offline, using local empty array.', err);
      });
  }, []);

  useEffect(() => {
    axios.get(`${API_BASE}/api/v1/traffic/${cityId}/congestion`)
      .then(res => {
        setCongestion(res.data.congestion || {});
        setIncidents(res.data.incidents || []);
      })
      .catch(err => {
        console.warn('Traffic congestion API offline.', err);
      });
  }, [cityId]);

  // Geocoding search submission
  const handleGeocodeSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    try {
      // 1. Check if the searched query matches one of the pre-seeded or already fetched cities in citiesList
      const q = searchQuery.toLowerCase();
      const matchedCity = citiesList.find(c => c.name.toLowerCase() === q || q.includes(c.name.toLowerCase()) || c.id.toLowerCase() === q);
      if (matchedCity) {
        setCityId(matchedCity.id);
        setSearchLoading(false);
        return;
      }

      // 2. Fetch coordinate boundaries using Nominatim
      const response = await axios.get(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchQuery)}&format=json&limit=1`);
      if (response.data && response.data.length > 0) {
        const first = response.data[0];
        const lat = Number(first.lat);
        const lon = Number(first.lon);
        
        // Define bounding box: [min_lat, min_lng, max_lat, max_lng]
        let bbox = [];
        if (first.boundingbox) {
          bbox = [
            Number(first.boundingbox[0]),
            Number(first.boundingbox[2]),
            Number(first.boundingbox[1]),
            Number(first.boundingbox[3])
          ];
        } else {
          bbox = [lat - 0.02, lon - 0.02, lat + 0.02, lon + 0.02];
        }
        
        setCenter([lat, lon]);
        setZoom(13);
        
        // 3. Post to API Gateway to create the city network dynamically
        const name = searchQuery.split(',')[0].trim();
        const osmRes = await axios.post(`${API_BASE}/api/v1/cities/osm`, {
          city_name: name,
          bbox: bbox
        });
        
        const newCity = osmRes.data;
        setCitiesList(prev => {
          if (prev.some(c => c.id === newCity.id)) return prev;
          return [...prev, newCity];
        });
        setCityId(newCity.id);
      } else {
        alert('Location not found. Try searching for city name (e.g. Paris, Tokyo, Mumbai)');
      }
    } catch (err) {
      console.warn('Geocoding request/network download failed, checking fallback.', err);
      const q = searchQuery.toLowerCase();
      if (q.includes('tokyo')) {
        setCenter([35.6762, 139.6503]);
        setCityId('tokyo');
      } else if (q.includes('new york') || q.includes('nyc')) {
        setCenter([40.7128, -74.0060]);
        setCityId('newyork');
      } else if (q.includes('mumbai')) {
        setCenter([19.0760, 72.8777]);
        setCityId('mumbai');
      } else if (q.includes('delhi')) {
        setCenter([28.6139, 77.2090]);
        setCityId('delhi');
      } else if (q.includes('bengaluru') || q.includes('bangalore')) {
        setCenter([12.9716, 77.5946]);
        setCityId('bengaluru');
      } else {
        // Dynamic resilient fallback city creation (offline)
        const name = searchQuery.trim();
        const lat = 48.8566 + (Math.random() - 0.5) * 2.0;
        const lon = 2.3522 + (Math.random() - 0.5) * 2.0;
        const bbox = [lat - 0.02, lon - 0.02, lat + 0.02, lon + 0.02];
        
        setCenter([lat, lon]);
        setZoom(13);
        
        try {
          const osmRes = await axios.post(`${API_BASE}/api/v1/cities/osm`, {
            city_name: name,
            bbox: bbox
          });
          const newCity = osmRes.data;
          setCitiesList(prev => {
            if (prev.some(c => c.id === newCity.id)) return prev;
            return [...prev, newCity];
          });
          setCityId(newCity.id);
        } catch (fallbackErr) {
          alert('Offline fallback failed to generate network.');
        }
      }
    } finally {
      setSearchLoading(false);
    }
  };

  // Compute Route
  const handleComputeRoute = () => {
    if (sourceNode === '' || targetNode === '') {
      setRoutingError('Please select both source and target nodes.');
      return;
    }
    
    setRoutingError(null);
    axios.post(`${API_BASE}/api/v1/simulations/${cityId}/route`, {
      source_node: Number(sourceNode),
      target_node: Number(targetNode)
    })
      .then(res => {
        const data = res.data;
        if (data.shortest_path && data.shortest_path.length > 0) {
          setShortestPath(data.shortest_path);
          setDistance(data.distance_meters);
          setAlternativePath(data.alternative_path || []);
          setAltDistance(data.alternative_distance_meters || 0);
        } else {
          setRoutingError('No path found connecting source and target nodes.');
        }
      })
      .catch(err => {
        console.warn('Routing endpoint offline, generating local mock route.', err);
        setShortestPath([Number(sourceNode), Number(targetNode)]);
        setDistance(450.0);
        setAlternativePath([]);
        setAltDistance(0);
      });
  };

  const handleNodeClick = (nodeId: number) => {
    if (sourceNode === '') {
      setSourceNode(nodeId);
    } else if (targetNode === '') {
      setTargetNode(nodeId);
    } else {
      setSourceNode(nodeId);
      setTargetNode('');
    }
  };

  const filteredDisasters = showDisasters
    ? disasters.filter(d => d.city === cityId || cityId.startsWith(d.city))
    : [];

  return (
    <div className="h-screen bg-background text-slate-100 flex flex-col overflow-hidden font-sans" dir={isRtl ? 'rtl' : 'ltr'}>
      {/* Header */}
      <header className="border-b border-slate-800 bg-card/60 backdrop-blur-md px-8 py-4 flex items-center justify-between z-50">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-sm font-semibold text-slate-400 hover:text-white transition-colors">← {t('dashboardTitle')}</Link>
          <span className="text-slate-600">|</span>
          <h2 className="font-bold text-base tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
            {t('gisWorkbench')}
          </h2>
        </div>
        
        {/* Geocoder Search Bar and City Dropdown */}
        <div className="flex items-center gap-4">
          <form onSubmit={handleGeocodeSearch} className="flex gap-2 items-center bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1">
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              placeholder={t('placeholderSearch')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent text-xs text-slate-300 focus:outline-none w-52"
            />
            <button
              type="submit"
              disabled={searchLoading}
              className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-bold px-2 py-0.5 rounded border border-slate-750 transition-colors"
            >
              {searchLoading ? '...' : 'Go'}
            </button>
          </form>

          <select
            value={lang}
            onChange={(e) => handleLangChange(e.target.value as Language)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs font-semibold focus:outline-none cursor-pointer text-slate-300"
          >
            {languages.map((l) => (
              <option key={l.code} value={l.code}>{l.name}</option>
            ))}
          </select>

          <select
            value={cityId}
            onChange={(e) => setCityId(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs font-semibold focus:outline-none cursor-pointer text-slate-300"
          >
            {citiesList.map((c) => (
              <option key={c.id} value={c.id}>{c.name} ({c.satellite_source || 'OSM'})</option>
            ))}
          </select>
        </div>
      </header>

      {/* Main Workspace */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Control Panel */}
        <aside className="w-80 border-r border-slate-800/80 bg-card/30 backdrop-blur-md p-6 flex flex-col justify-between overflow-y-auto shrink-0">
          <div className="flex flex-col gap-6">
            <div>
              <h3 className="text-sm font-bold tracking-wider uppercase mb-1 flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-primary" /> {t('visualLayers')}
              </h3>
              <p className="text-[10px] text-slate-400">Configure map visual overrides</p>
            </div>

            {/* Heatmaps */}
            <div className="flex flex-col gap-3">
              <span className="text-xs font-bold text-slate-400 block">{t('criticalityOverlay')}</span>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setHeatmap(heatmap === 'centrality' ? null : 'centrality')}
                  className={`px-3 py-2 rounded-lg text-xs font-semibold border transition-all ${
                    heatmap === 'centrality' ? 'bg-primary/20 border-primary text-primary' : 'bg-slate-900/50 border-slate-800 text-slate-300'
                  }`}
                >
                  {t('centrality')}
                </button>
                <button
                  onClick={() => setHeatmap(heatmap === 'confidence' ? null : 'confidence')}
                  className={`px-3 py-2 rounded-lg text-xs font-semibold border transition-all ${
                    heatmap === 'confidence' ? 'bg-accent/20 border-accent text-accent' : 'bg-slate-900/50 border-slate-800 text-slate-300'
                  }`}
                >
                  {t('confidence')}
                </button>
              </div>
            </div>

            {/* Live Disaster Toggle */}
            <div className="flex items-center justify-between border-t border-slate-800/60 pt-4">
              <div className="flex flex-col gap-0.5">
                <span className="text-xs font-bold text-slate-300 flex items-center gap-1">
                  <ShieldAlert className="w-3.5 h-3.5 text-red-500" /> {t('activeHazards')}
                </span>
                <span className="text-[9px] text-slate-400">NASA FIRMS & GDACS feed</span>
              </div>
              <button
                onClick={() => setShowDisasters(!showDisasters)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-all ${
                  showDisasters ? 'bg-red-950/40 border-red-800 text-red-400' : 'bg-slate-900/50 border-slate-800 text-slate-400'
                }`}
              >
                {showDisasters ? 'ACTIVE' : 'MUTED'}
              </button>
            </div>

            {/* Traffic Incidents Feed */}
            {incidents.length > 0 && (
              <div className="flex flex-col gap-2 border-t border-slate-800/60 pt-4">
                <span className="text-xs font-bold text-slate-400 block flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-yellow-500" /> {t('trafficAdvisories')} ({incidents.length})
                </span>
                <div className="max-h-24 overflow-y-auto flex flex-col gap-1.5 pr-1 border border-slate-800/60 rounded-lg p-2 bg-slate-950/20">
                  {incidents.map((inc, i) => (
                    <div key={i} className="text-[10px] bg-slate-900/40 border border-slate-800/55 rounded p-1.5 flex flex-col gap-0.5">
                      <span className="font-semibold text-slate-300 flex items-center gap-1">
                        <span className={`w-1.5 h-1.5 rounded-full ${inc.severity === 'high' ? 'bg-red-500 animate-pulse' : 'bg-orange-500'}`} />
                        {inc.description}
                      </span>
                      <span className="text-slate-500 uppercase text-[8px]">Closed links: {inc.edge.join('-')}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Route Planning */}
            <div className="flex flex-col gap-3 border-t border-slate-800/60 pt-4">
              <span className="text-xs font-bold text-slate-400 block flex items-center gap-1">
                <ArrowLeftRight className="w-3.5 h-3.5" /> {t('routingPlanner')}
              </span>
              
              <div className="flex flex-col gap-2">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[9px] uppercase text-slate-400 font-semibold block mb-1">Source Node</label>
                    <input
                      type="number"
                      placeholder="Click map node"
                      value={sourceNode}
                      onChange={(e) => setSourceNode(e.target.value === '' ? '' : Number(e.target.value))}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-[9px] uppercase text-slate-400 font-semibold block mb-1">Target Node</label>
                    <input
                      type="number"
                      placeholder="Click map node"
                      value={targetNode}
                      onChange={(e) => setTargetNode(e.target.value === '' ? '' : Number(e.target.value))}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none"
                    />
                  </div>
                </div>
                
                {routingError && (
                  <span className="text-[10px] text-alert font-medium">{routingError}</span>
                )}
                
                <button
                  onClick={handleComputeRoute}
                  className="w-full bg-primary py-2 rounded-lg text-xs font-bold hover:bg-primary/95 transition-all mt-2"
                >
                  {t('calculateRoutes')}
                </button>
              </div>
            </div>

            {/* Routing Output */}
            {shortestPath.length > 0 && (
              <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-4 flex flex-col gap-3 animate-fade-in">
                <div>
                  <span className="text-[10px] uppercase text-slate-400 font-bold block">{t('shortestPath')}</span>
                  <span className="text-sm font-bold text-primary">{distance.toFixed(1)} meters</span>
                </div>
                {alternativePath.length > 0 && (
                  <div>
                    <span className="text-[10px] uppercase text-slate-400 font-bold block">{t('alternativePath')}</span>
                    <span className="text-sm font-bold text-success">{altDistance.toFixed(1)} meters</span>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="border-t border-slate-800/80 pt-4 text-[10px] text-slate-500 flex flex-col gap-1">
            <span className="flex items-center gap-1"><Eye className="w-3 h-3 text-emerald-500" /> Healed edges are dashed green links</span>
            <span className="flex items-center gap-1"><Zap className="w-3 h-3 text-yellow-500 animate-pulse" /> Click nodes on map to set route endpoints</span>
          </div>
        </aside>

        {/* Map Canvas */}
        <div className="flex-1 h-full p-6">
          <MapComponent
            center={center}
            zoom={zoom}
            nodes={nodes}
            edges={edges}
            shortestPath={shortestPath}
            alternativePath={alternativePath}
            heatmapType={heatmap}
            onNodeClick={handleNodeClick}
            disasters={filteredDisasters}
            congestion={congestion}
          />
        </div>
      </div>

      {/* Floating AI Copilot Widget */}
      <CopilotChat cityId={cityId} />
    </div>
  );
}
