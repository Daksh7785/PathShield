import React, { useState } from 'react';
import Link from 'next/link';
import { Activity, Code, Server, ShieldCheck, Zap, Play, Terminal, Database, Copy, Check } from 'lucide-react';

interface ApiEndpoint {
  name: string;
  method: 'GET' | 'POST';
  path: string;
  description: string;
  requestBody?: string;
  responseBody: string;
}

export default function MarketplacePage() {
  const [activeTab, setActiveTab] = useState<'apis' | 'analytics'>('apis');
  const [selectedApiIndex, setSelectedApiIndex] = useState<number>(0);
  const [copied, setCopied] = useState(false);
  const [apiResponse, setApiResponse] = useState<string | null>(null);
  const [apiLoading, setApiLoading] = useState(false);

  const apis: ApiEndpoint[] = [
    {
      name: 'Road Extraction API',
      method: 'POST',
      path: '/api/v1/extract',
      description: 'Extracts road networks from raw multi-satellite (Cartosat, Sentinel) imagery.',
      requestBody: JSON.stringify({
        satellite_source: 'Cartosat-3',
        coordinates: [12.97, 77.59],
        image_base64: 'iVBORw0KGgoAAAANS...'
      }, null, 2),
      responseBody: JSON.stringify({
        status: 'success',
        extraction_score_iou: 0.892,
        road_mask_url: 'https://storage.routeguard.ai/masks/temp_mask.png',
        metadata: {
          satellite: 'Cartosat-3',
          resolution_meters: 0.28,
          timestamp: new Date().toISOString()
        }
      }, null, 2)
    },
    {
      name: 'Topological Graph API',
      method: 'POST',
      path: '/api/v1/graph/generate',
      description: 'Converts road masks into centerline vector graph files (Nodes, Edges).',
      requestBody: JSON.stringify({
        mask_url: 'https://storage.routeguard.ai/masks/temp_mask.png',
        simplify_tolerance_meters: 1.5
      }, null, 2),
      responseBody: JSON.stringify({
        nodes_count: 142,
        edges_count: 218,
        graph_geojson: {
          type: 'FeatureCollection',
          features: [
            { type: 'Feature', geometry: { type: 'Point', coordinates: [77.594, 12.971] }, properties: { id: 0, node_type: 'intersection' } }
          ]
        }
      }, null, 2)
    },
    {
      name: 'Resilience Index API',
      method: 'GET',
      path: '/api/v1/resilience/bengaluru',
      description: 'Retrieves global urban resilience and articulation metrics for a city.',
      responseBody: JSON.stringify({
        city: 'Bengaluru',
        resilience_index: 0.854,
        critical_junctions_count: 14,
        redundancy_score: 0.792,
        articulation_points: [12, 45, 87],
        evaluation_timestamp: new Date().toISOString()
      }, null, 2)
    },
    {
      name: 'Traffic Routing API',
      method: 'POST',
      path: '/api/v1/routing/route',
      description: 'Calculates the optimal traffic-aware route and alternative detour options.',
      requestBody: JSON.stringify({
        cityId: 'bengaluru',
        source_node: 12,
        target_node: 85,
        avoid_nodes: [45]
      }, null, 2),
      responseBody: JSON.stringify({
        shortest_path: [12, 14, 19, 85],
        distance_meters: 450.0,
        estimated_time_seconds: 480,
        alternative_path: [12, 10, 85],
        alternative_distance_meters: 610.0,
        congestion_index: 'moderate'
      }, null, 2)
    }
  ];

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleTestApi = () => {
    setApiLoading(true);
    setApiResponse(null);
    setTimeout(() => {
      setApiResponse(apis[selectedApiIndex].responseBody);
      setApiLoading(false);
    }, 800);
  };

  return (
    <div className="min-h-screen bg-background text-slate-100 flex flex-col font-sans">
      {/* Premium Header */}
      <header className="border-b border-slate-800 bg-card/60 backdrop-blur-md px-8 py-5 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary to-accent flex items-center justify-center shadow-lg shadow-primary/20">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
              PATHSHIELD
            </h1>
            <p className="text-[10px] tracking-widest text-accent uppercase font-semibold">
              Route Resilience & Urban Mobility Intelligence
            </p>
          </div>
        </div>
        <nav className="flex items-center gap-6">
          <Link href="/" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Overview</Link>
          <Link href="/gis" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">GIS Map</Link>
          <Link href="/simulation" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Simulations</Link>
          <Link href="/rankings" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Planning AI</Link>
          <Link href="/marketplace" className="text-sm font-medium text-primary hover:text-white transition-colors">API Marketplace</Link>
        </nav>
      </header>

      {/* Main Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-8 py-12 flex flex-col gap-8">
        {/* Toggle tabs */}
        <div className="flex justify-between items-center border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-2xl font-bold tracking-wide">Developer Hub & SaaS Marketplace</h2>
            <p className="text-xs text-slate-400">Deploy serverless GIS & Graph operations inside your own software suites</p>
          </div>
          <div className="bg-slate-900 p-1 rounded-xl border border-slate-800 flex gap-2">
            <button
              onClick={() => setActiveTab('apis')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'apis' ? 'bg-primary text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Developer APIs
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'analytics' ? 'bg-primary text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              SaaS Analytics
            </button>
          </div>
        </div>

        {activeTab === 'apis' ? (
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Sidebar list */}
            <div className="flex flex-col gap-3">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-1">Endpoints</span>
              {apis.map((api, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setSelectedApiIndex(idx);
                    setApiResponse(null);
                  }}
                  className={`p-4 rounded-xl text-left border transition-all ${
                    selectedApiIndex === idx ? 'bg-slate-900 border-primary' : 'bg-slate-950/40 border-slate-850 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold">{api.name}</span>
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded ${
                      api.method === 'POST' ? 'bg-primary/20 text-primary' : 'bg-success/20 text-success'
                    }`}>
                      {api.method}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400">{api.description}</p>
                </button>
              ))}
            </div>

            {/* API Playground / Sandbox */}
            <div className="lg:col-span-2 flex flex-col gap-6 bg-slate-900/40 border border-slate-800 p-6 rounded-2xl">
              <div>
                <h3 className="text-base font-bold mb-1 flex items-center gap-1.5">
                  <Terminal className="w-4 h-4 text-primary" /> API Request Playground
                </h3>
                <code className="text-xs font-mono text-slate-300 bg-slate-950 px-2 py-1 rounded select-all">
                  {apis[selectedApiIndex].method} http://localhost:8000{apis[selectedApiIndex].path}
                </code>
              </div>

              {apis[selectedApiIndex].requestBody && (
                <div className="flex flex-col gap-2">
                  <div className="flex justify-between items-center text-xs text-slate-400 font-semibold">
                    <span>Request Body (JSON)</span>
                    <button
                      onClick={() => handleCopy(apis[selectedApiIndex].requestBody || '')}
                      className="hover:text-white flex items-center gap-1"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
                      Copy
                    </button>
                  </div>
                  <pre className="bg-slate-950/80 p-4 rounded-xl border border-slate-850 text-[11px] font-mono overflow-x-auto text-slate-300 max-h-40">
                    {apis[selectedApiIndex].requestBody}
                  </pre>
                </div>
              )}

              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-500 font-semibold">API Key Authenticated via Bearer JWT Token</span>
                <button
                  onClick={handleTestApi}
                  disabled={apiLoading}
                  className="bg-primary hover:bg-primary/95 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-1.5 transition-all shadow-lg shadow-primary/20"
                >
                  <Play className="w-3.5 h-3.5" />
                  {apiLoading ? 'Invoking...' : 'Test Request'}
                </button>
              </div>

              {/* Response output */}
              {apiResponse && (
                <div className="flex flex-col gap-2 border-t border-slate-800 pt-5 animate-fade-in">
                  <span className="text-xs text-slate-400 font-semibold">Response Headers: HTTP 200 OK</span>
                  <pre className="bg-slate-950 p-4 rounded-xl border border-slate-850 text-[11px] font-mono overflow-x-auto text-slate-300 max-h-60">
                    {apiResponse}
                  </pre>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="grid md:grid-cols-3 gap-6">
            <div className="glass-panel p-6 rounded-2xl flex flex-col gap-1.5 border border-slate-800">
              <span className="text-xs text-slate-400 font-bold block">Total API Invocations (This Month)</span>
              <span className="text-3xl font-extrabold text-primary">1,482,904</span>
              <span className="text-[10px] text-success font-semibold">↑ 14.8% vs last month</span>
            </div>
            <div className="glass-panel p-6 rounded-2xl flex flex-col gap-1.5 border border-slate-800">
              <span className="text-xs text-slate-400 font-bold block">Average API Latency</span>
              <span className="text-3xl font-extrabold text-success">42ms</span>
              <span className="text-[10px] text-slate-500 font-semibold">Optimized via Redis Cache & PostGIS index</span>
            </div>
            <div className="glass-panel p-6 rounded-2xl flex flex-col gap-1.5 border border-slate-800">
              <span className="text-xs text-slate-400 font-bold block">Active Subscriptions</span>
              <span className="text-3xl font-extrabold text-accent">18 Organizations</span>
              <span className="text-[10px] text-slate-500 font-semibold">ISRO, NRSC, Delhi Planning Commission</span>
            </div>
            
            {/* Enterprise Roles / RBAC Table */}
            <div className="md:col-span-3 bg-slate-900/40 border border-slate-800 rounded-2xl p-6 flex flex-col gap-4 mt-4">
              <div>
                <h4 className="font-bold text-sm">Organization Role Based Access Controls (RBAC)</h4>
                <p className="text-[10px] text-slate-400">Configure roles for multi-tenant teams and municipal agencies</p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="py-2.5">User</th>
                      <th className="py-2.5">Role</th>
                      <th className="py-2.5">Municipal Scope</th>
                      <th className="py-2.5">API Access</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-slate-800/50">
                      <td className="py-2.5 font-medium text-slate-200">daksh@isro.gov.in</td>
                      <td className="py-2.5"><span className="bg-primary/20 text-primary px-2 py-0.5 rounded font-semibold text-[10px]">Scientist</span></td>
                      <td className="py-2.5 text-slate-400">Bengaluru & Delhi Urban Maps</td>
                      <td className="py-2.5 text-slate-400">Unrestricted Ingestion & Extraction</td>
                    </tr>
                    <tr className="border-b border-slate-800/50">
                      <td className="py-2.5 font-medium text-slate-200">planning@bbmp.gov.in</td>
                      <td className="py-2.5"><span className="bg-accent/20 text-accent px-2 py-0.5 rounded font-semibold text-[10px]">Planner</span></td>
                      <td className="py-2.5 text-slate-400">Bengaluru BBMP Scope</td>
                      <td className="py-2.5 text-slate-400">Routing & Planning Recommendations</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 font-medium text-slate-200">officer@ndma.gov.in</td>
                      <td className="py-2.5"><span className="bg-red-500/20 text-red-400 px-2 py-0.5 rounded font-semibold text-[10px]">Incident Commander</span></td>
                      <td className="py-2.5 text-slate-400">All India Disaster Domains</td>
                      <td className="py-2.5 text-slate-400">Evacuation & Stress Simulations</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-8 text-center text-xs text-slate-500">
        <p>© 2026 PathShield Urban Intelligence Platform. Cartosat & Remote Sensing mandating authority: ISRO/NRSC.</p>
      </footer>
    </div>
  );
}
