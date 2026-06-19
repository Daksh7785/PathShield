import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Activity, Map, ShieldAlert, Award, FileText, ChevronRight, BarChart2 } from 'lucide-react';
import axios from 'axios';

interface CityMetadata {
  id: string;
  name: string;
  state: string;
  country: string;
  population: number;
  area_sqkm: number;
  satellite_source: string;
  resolution_m: number;
  total_nodes: number;
  total_edges: number;
  network_resilience_index: number;
}

export default function IndexPage() {
  const [cities, setCities] = useState<CityMetadata[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch cities from backend
    axios.get('http://localhost:8000/api/v1/cities')
      .then(res => {
        setCities(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.warn('Backend connection failed, using local mock cities.', err);
        // Direct local mock if backend server is not running yet
        setCities([
          {
            id: 'bengaluru-id',
            name: 'Bengaluru',
            state: 'Karnataka',
            country: 'India',
            population: 12000000,
            area_sqkm: 741.0,
            satellite_source: 'Cartosat-3',
            resolution_m: 0.28,
            total_nodes: 500,
            total_edges: 800,
            network_resilience_index: 0.854
          },
          {
            id: 'delhi-id',
            name: 'Delhi',
            state: 'Delhi',
            country: 'India',
            population: 31000000,
            area_sqkm: 1484.0,
            satellite_source: 'Sentinel-2',
            resolution_m: 10.0,
            total_nodes: 120,
            total_edges: 180,
            network_resilience_index: 0.812
          }
        ]);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-background text-slate-100 flex flex-col">
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
          <Link href="/" className="text-sm font-medium text-primary hover:text-white transition-colors">Overview</Link>
          <Link href="/gis" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">GIS Map</Link>
          <Link href="/simulation" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Simulations</Link>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-8 py-12 flex flex-col gap-12">
        <section className="relative rounded-3xl p-8 overflow-hidden border border-slate-800 bg-gradient-to-br from-card to-background">
          <div className="absolute top-0 right-0 w-96 h-96 bg-primary/5 rounded-full filter blur-[80px]" />
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-accent/5 rounded-full filter blur-[80px]" />
          
          <div className="max-w-2xl relative z-10">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-accent/10 text-accent border border-accent/20 mb-4">
              <Award className="w-3.5 h-3.5" /> ISRO Hackathon Problem Statement 4
            </span>
            <h2 className="text-4xl font-extrabold tracking-tight mb-4">
              Occlusion-Robust Road Extraction & Network Resilience
            </h2>
            <p className="text-slate-400 leading-relaxed mb-6">
              PathShield processes high-resolution satellite imagery (Cartosat-3 / Sentinel-2) using advanced Deep Learning, heals connectivity gaps caused by canopies and shadows, builds topology networks, and conducts real-time urban disaster simulations.
            </p>
            <div className="flex gap-4">
              <Link href="/gis" className="inline-flex items-center justify-center px-5 py-3 rounded-xl bg-primary text-sm font-semibold hover:bg-primary/95 transition-all shadow-lg shadow-primary/20">
                Launch GIS Workbench <ChevronRight className="w-4 h-4 ml-1" />
              </Link>
              <Link href="/simulation" className="inline-flex items-center justify-center px-5 py-3 rounded-xl bg-slate-800 text-sm font-semibold hover:bg-slate-700 transition-colors">
                Run Stress Simulations
              </Link>
            </div>
          </div>
        </section>

        {/* Cities Section */}
        <section className="flex flex-col gap-6">
          <div>
            <h3 className="text-xl font-bold tracking-wide">Urban Networks</h3>
            <p className="text-xs text-slate-400">Select a city to view topological stats and resilience heatmaps</p>
          </div>

          {loading ? (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-6">
              {cities.map(city => (
                <div key={city.id} className="glass-panel p-6 rounded-2xl flex flex-col justify-between hover:border-slate-700 transition-all group">
                  <div>
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h4 className="text-lg font-bold group-hover:text-primary transition-colors">{city.name}</h4>
                        <p className="text-xs text-slate-400">{city.state}, {city.country}</p>
                      </div>
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                        city.network_resilience_index > 0.8 ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'
                      }`}>
                        Resilience: {(city.network_resilience_index * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 my-6">
                      <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                        <span className="text-[10px] uppercase text-slate-400 block font-semibold">Total Nodes</span>
                        <span className="text-xl font-bold">{city.total_nodes}</span>
                      </div>
                      <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                        <span className="text-[10px] uppercase text-slate-400 block font-semibold">Total Edges</span>
                        <span className="text-xl font-bold">{city.total_edges}</span>
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-slate-800/80 pt-4 flex justify-between items-center text-xs text-slate-400">
                    <span>Sat Source: {city.satellite_source} ({city.resolution_m}m)</span>
                    <Link href={`/gis?city=${city.name.toLowerCase()}`} className="text-primary font-semibold hover:underline inline-flex items-center gap-1">
                      Explore Map <ChevronRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Feature Highlights */}
        <section className="grid md:grid-cols-3 gap-6">
          <div className="glass-panel p-6 rounded-2xl flex flex-col gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
              <Map className="w-5 h-5" />
            </div>
            <h4 className="font-bold">Occlusion-Robust Extraction</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Handles tree canopies, shadows, cloud covers, and buildings using multi-scale transformers (ViT-B/32, SegFormer) to ensure zero spectrally blind spots.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl flex flex-col gap-3">
            <div className="w-10 h-10 rounded-xl bg-accent/10 text-accent flex items-center justify-center">
              <Activity className="w-5 h-5" />
            </div>
            <h4 className="font-bold">Topological Gap Healing</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Uses disjoint sets, union-find algorithms, and angular-continuity vector heuristics to bridge gaps and heal fragmented network skeletons automatically.
            </p>
          </div>

          <div className="glass-panel p-6 rounded-2xl flex flex-col gap-3">
            <div className="w-10 h-10 rounded-xl bg-alert/10 text-alert flex items-center justify-center">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <h4 className="font-bold">Disaster Resilience Simulations</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Simulate flood inundations, route blockages, bridge collapses, and cascading failures to identify single points of failure and bottlenecks.
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-8 text-center text-xs text-slate-500">
        <p>© 2026 PathShield Urban Intelligence Platform. Cartosat & Remote Sensing mandating authority: ISRO/NRSC.</p>
      </footer>
    </div>
  );
}
