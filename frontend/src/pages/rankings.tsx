import React, { useState } from 'react';
import Link from 'next/link';
import { Activity, BarChart2, ShieldAlert, Award, FileText, ChevronRight, HelpCircle, Download, FileSpreadsheet, Layers, Sparkles } from 'lucide-react';

interface CityRanking {
  rank: number;
  name: string;
  country: string;
  resilienceIndex: number;
  accessibilityScore: number;
  connectivityScore: number;
  readinessScore: number;
}

export default function RankingsPage() {
  const [activeSegment, setActiveSegment] = useState<'rankings' | 'planning' | 'reports'>('rankings');
  
  // Smart planning inputs
  const [sourceNode, setSourceNode] = useState('12');
  const [targetNode, setTargetNode] = useState('45');
  const [projectType, setProjectType] = useState<'flyover' | 'bridge' | 'road'>('flyover');
  const [planResult, setPlanResult] = useState<any | null>(null);
  const [planningLoading, setPlanningLoading] = useState(false);

  const rankings: CityRanking[] = [
    { rank: 1, name: 'New York', country: 'United States', resilienceIndex: 0.912, accessibilityScore: 0.88, connectivityScore: 0.93, readinessScore: 0.89 },
    { rank: 2, name: 'Tokyo', country: 'Japan', resilienceIndex: 0.884, accessibilityScore: 0.89, connectivityScore: 0.90, readinessScore: 0.92 },
    { rank: 3, name: 'Bengaluru', country: 'India', resilienceIndex: 0.854, accessibilityScore: 0.76, connectivityScore: 0.81, readinessScore: 0.74 },
    { rank: 4, name: 'Delhi', country: 'India', resilienceIndex: 0.812, accessibilityScore: 0.72, connectivityScore: 0.78, readinessScore: 0.71 },
    { rank: 5, name: 'Mumbai', country: 'India', resilienceIndex: 0.785, accessibilityScore: 0.69, connectivityScore: 0.75, readinessScore: 0.68 }
  ];

  const handleRunPlanningAI = (e: React.FormEvent) => {
    e.preventDefault();
    setPlanningLoading(true);
    setPlanResult(null);

    setTimeout(() => {
      const isFlyover = projectType === 'flyover';
      setPlanResult({
        costEstimatedCr: isFlyover ? 145 : 85,
        resilienceGainPct: isFlyover ? 14.8 : 8.2,
        affectedPopulationWorldPop: isFlyover ? '120,400 residents' : '45,200 residents',
        fuelLossReductionLtrsDaily: isFlyover ? 1200 : 450,
        businessImpactCrYearly: isFlyover ? 24.5 : 8.6,
        roiMonths: isFlyover ? 36 : 48,
        recommendation: isFlyover
          ? "HIGH PRIORITY — Constructing a flyover corridor between Node 12 and 45 will decongest the Central Ring corridor, offering a 14.8% net resilience improvement and securing alternate transit routes for 120k citizens during monsoon flooding closures."
          : "MEDIUM PRIORITY — Consider widening lanes or adding dynamic traffic signals before committing to bridge structural changes."
      });
      setPlanningLoading(false);
    }, 1000);
  };

  const triggerExport = (format: string) => {
    alert(`Generating RouteGuard AI municipal report in ${format.toUpperCase()} format. Download should begin shortly.`);
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
          <Link href="/rankings" className="text-sm font-medium text-primary hover:text-white transition-colors">Planning AI</Link>
          <Link href="/marketplace" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">API Marketplace</Link>
        </nav>
      </header>

      {/* Main Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-8 py-12 flex flex-col gap-8">
        {/* Navigation Tabs */}
        <div className="flex justify-between items-center border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-2xl font-bold tracking-wide">Urban Benchmarking & Planning Center</h2>
            <p className="text-xs text-slate-400">Measure resilience ratios and build smart infrastructure recommendations</p>
          </div>
          <div className="bg-slate-900 p-1 rounded-xl border border-slate-800 flex gap-2">
            <button
              onClick={() => setActiveSegment('rankings')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeSegment === 'rankings' ? 'bg-primary text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Resilience Rankings
            </button>
            <button
              onClick={() => setActiveSegment('planning')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeSegment === 'planning' ? 'bg-primary text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Smart Planning AI
            </button>
            <button
              onClick={() => setActiveSegment('reports')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeSegment === 'reports' ? 'bg-primary text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Export Center
            </button>
          </div>
        </div>

        {activeSegment === 'rankings' ? (
          <div className="flex flex-col gap-6">
            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6">
              <h3 className="font-bold text-sm mb-3">Global Resiliency Benchmark Index</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="py-3 pl-4">Rank</th>
                      <th className="py-3">City</th>
                      <th className="py-3">Country</th>
                      <th className="py-3">Resilience Index</th>
                      <th className="py-3">Accessibility</th>
                      <th className="py-3">Connectivity</th>
                      <th className="py-3">Emergency Readiness</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rankings.map((c, i) => (
                      <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-900/30 transition-colors">
                        <td className="py-3.5 pl-4 font-bold text-primary">{c.rank}</td>
                        <td className="py-3.5 font-bold text-slate-200">{c.name}</td>
                        <td className="py-3.5 text-slate-400">{c.country}</td>
                        <td className="py-3.5">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            c.resilienceIndex > 0.85 ? 'bg-success/15 text-success' : 'bg-warning/15 text-warning'
                          }`}>
                            {(c.resilienceIndex * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-3.5 text-slate-300">{(c.accessibilityScore * 100).toFixed(0)}%</td>
                        <td className="py-3.5 text-slate-300">{(c.connectivityScore * 100).toFixed(0)}%</td>
                        <td className="py-3.5 text-slate-300">{(c.readinessScore * 100).toFixed(0)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : activeSegment === 'planning' ? (
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Control Form */}
            <form onSubmit={handleRunPlanningAI} className="bg-slate-900/40 border border-slate-800 p-6 rounded-2xl flex flex-col gap-4">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-1">Planning Parameters</h3>
                <p className="text-[10px] text-slate-500">Formulate flyover or bridge ROI calculations</p>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] text-slate-400 font-semibold uppercase">Proposed Location Start</label>
                <input
                  type="number"
                  value={sourceNode}
                  onChange={(e) => setSourceNode(e.target.value)}
                  className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] text-slate-400 font-semibold uppercase">Proposed Location End</label>
                <input
                  type="number"
                  value={targetNode}
                  onChange={(e) => setTargetNode(e.target.value)}
                  className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] text-slate-400 font-semibold uppercase">Infrastructure Project Type</label>
                <select
                  value={projectType}
                  onChange={(e) => setProjectType(e.target.value as any)}
                  className="bg-slate-950 border border-slate-850 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none cursor-pointer"
                >
                  <option value="flyover">Arterial Flyover Corridor</option>
                  <option value="bridge">Topological Gap Bridge</option>
                  <option value="road">Alternate Bypass Street</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={planningLoading}
                className="bg-primary hover:bg-primary/95 text-white font-bold text-xs py-2.5 rounded-lg flex items-center justify-center gap-1.5 transition-all shadow-lg shadow-primary/20"
              >
                <Sparkles className="w-3.5 h-3.5" />
                {planningLoading ? 'Evaluating Urban Graph...' : 'Generate Planning Recommendation'}
              </button>
            </form>

            {/* Smart Planning AI Output */}
            <div className="lg:col-span-2 bg-slate-900/40 border border-slate-850 p-6 rounded-2xl flex flex-col justify-between">
              {planResult ? (
                <div className="flex flex-col gap-6 animate-fade-in">
                  <div>
                    <h3 className="text-base font-bold text-slate-200 mb-1">Smart City ROI & Impact Analysis</h3>
                    <p className="text-[10px] text-slate-500">Evaluated against WorldPop census and GHSL footprint data layers</p>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-850">
                      <span className="text-[9px] uppercase text-slate-400 block font-semibold">Resilience Gain</span>
                      <span className="text-lg font-bold text-success">+{planResult.resilienceGainPct}%</span>
                    </div>
                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-850">
                      <span className="text-[9px] uppercase text-slate-400 block font-semibold">Estimated Cost</span>
                      <span className="text-lg font-bold text-primary">₹{planResult.costEstimatedCr} Cr</span>
                    </div>
                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-850">
                      <span className="text-[9px] uppercase text-slate-400 block font-semibold">Affected Population</span>
                      <span className="text-sm font-bold text-slate-200 block pt-1">{planResult.affectedPopulationWorldPop}</span>
                    </div>
                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-850">
                      <span className="text-[9px] uppercase text-slate-400 block font-semibold">Daily Fuel Saved</span>
                      <span className="text-sm font-bold text-slate-200 block pt-1">{planResult.fuelLossReductionLtrsDaily} Litres</span>
                    </div>
                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-850">
                      <span className="text-[9px] uppercase text-slate-400 block font-semibold">Economic Gain (Yr)</span>
                      <span className="text-sm font-bold text-success block pt-1">₹{planResult.businessImpactCrYearly} Cr</span>
                    </div>
                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-850">
                      <span className="text-[9px] uppercase text-slate-400 block font-semibold">ROI Period</span>
                      <span className="text-sm font-bold text-accent block pt-1">{planResult.roiMonths} Months</span>
                    </div>
                  </div>

                  <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-850">
                    <span className="text-[10px] text-slate-400 font-bold uppercase block mb-1">AI Recommendation</span>
                    <p className="text-xs text-slate-300 leading-relaxed font-mono">{planResult.recommendation}</p>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
                  <HelpCircle className="w-10 h-10 text-slate-500 mb-2" />
                  <span className="text-xs text-slate-400 font-bold">Awaiting Planning Input</span>
                  <p className="text-[10px] text-slate-500 max-w-xs mt-1">Specify source/target nodes and project type to compute network-wide structural improvements</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-slate-900/40 border border-slate-850 p-6 rounded-2xl flex flex-col gap-6">
            <div>
              <h3 className="font-bold text-base mb-1">Exportable Municipal Report Formats</h3>
              <p className="text-xs text-slate-400">Generate executive briefs, routing files, and geographic GIS layers for external systems</p>
            </div>
            
            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6">
              <button
                onClick={() => triggerExport('pdf')}
                className="bg-slate-950 border border-slate-850 p-5 rounded-2xl text-left hover:border-primary transition-all flex flex-col justify-between h-36"
              >
                <div className="w-9 h-9 rounded-lg bg-red-500/10 text-red-400 flex items-center justify-center mb-4">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-xs font-bold block mb-0.5">Executive PDF Summary</span>
                  <p className="text-[9px] text-slate-500">Includes centrality graphs, flood perimeters and ROI recommendations.</p>
                </div>
              </button>

              <button
                onClick={() => triggerExport('excel')}
                className="bg-slate-950 border border-slate-850 p-5 rounded-2xl text-left hover:border-primary transition-all flex flex-col justify-between h-36"
              >
                <div className="w-9 h-9 rounded-lg bg-green-500/10 text-green-400 flex items-center justify-center mb-4">
                  <FileSpreadsheet className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-xs font-bold block mb-0.5">Topological Excel Statistics</span>
                  <p className="text-[9px] text-slate-500">Complete node-by-node valency, centrality index, and loss ratios.</p>
                </div>
              </button>

              <button
                onClick={() => triggerExport('geojson')}
                className="bg-slate-950 border border-slate-850 p-5 rounded-2xl text-left hover:border-primary transition-all flex flex-col justify-between h-36"
              >
                <div className="w-9 h-9 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center mb-4">
                  <Layers className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-xs font-bold block mb-0.5">Centerline GeoJSON Layer</span>
                  <p className="text-[9px] text-slate-500">Routable road skeleton vector files compatible with QGIS and ArcGIS.</p>
                </div>
              </button>
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
