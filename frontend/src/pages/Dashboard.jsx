import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Shield, Radio, Target, Zap, AlertTriangle, Activity, 
  MessageSquare, Settings, Map, BarChart3, Clock, ChevronRight,
  Radar, Crosshair, Waves, Send, RefreshCw
} from "lucide-react";
import { toast } from "sonner";
import BattleMap from "../components/BattleMap";
import ThreatPanel from "../components/ThreatPanel";
import AIConsole from "../components/AIConsole";
import MetricsPanel from "../components/MetricsPanel";
import ScenarioSelector from "../components/ScenarioSelector";
import CountermeasurePanel from "../components/CountermeasurePanel";
import ThreatTimeline from "../components/ThreatTimeline";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Dashboard = () => {
  const [emitters, setEmitters] = useState([]);
  const [threats, setThreats] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [activeScenario, setActiveScenario] = useState(null);
  const [selectedEmitter, setSelectedEmitter] = useState(null);
  const [activePanel, setActivePanel] = useState("threats");
  const [isLoading, setIsLoading] = useState(true);
  const [systemTime, setSystemTime] = useState(new Date());

  // Fetch initial data
  const fetchData = useCallback(async () => {
    try {
      const [emittersRes, threatsRes, metricsRes] = await Promise.all([
        axios.get(`${API}/emitters`),
        axios.get(`${API}/threats/assess`),
        axios.get(`${API}/metrics`)
      ]);
      
      setEmitters(emittersRes.data);
      setThreats(threatsRes.data);
      setMetrics(metricsRes.data);
      setIsLoading(false);
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("Failed to connect to AEGIS MIND backend");
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    
    // Update system time every second
    const timeInterval = setInterval(() => {
      setSystemTime(new Date());
    }, 1000);

    // Refresh data every 5 seconds
    const dataInterval = setInterval(fetchData, 5000);

    return () => {
      clearInterval(timeInterval);
      clearInterval(dataInterval);
    };
  }, [fetchData]);

  const handleScenarioActivate = async (scenarioId) => {
    try {
      const response = await axios.post(`${API}/scenarios/${scenarioId}/activate`);
      setActiveScenario(response.data);
      toast.success(`Scenario activated: ${response.data.emitters_loaded} emitters loaded`);
      fetchData();
    } catch (error) {
      toast.error("Failed to activate scenario");
    }
  };

  const handleEmitterSelect = (emitter) => {
    setSelectedEmitter(emitter);
    setActivePanel("analysis");
  };

  const formatTime = (date) => {
    return date.toISOString().replace('T', ' ').substring(0, 19) + 'Z';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a1628] flex items-center justify-center">
        <div className="text-center">
          <div className="relative w-24 h-24 mx-auto mb-6">
            <div className="absolute inset-0 border-2 border-teal-500/30 rounded-full"></div>
            <div className="absolute inset-2 border-2 border-teal-500/50 rounded-full radar-sweep"></div>
            <div className="absolute inset-4 border-2 border-teal-500 rounded-full"></div>
            <Radar className="absolute inset-0 m-auto w-8 h-8 text-teal-500" />
          </div>
          <h2 className="text-xl font-bold text-slate-100 tracking-wider uppercase">PROJEK HALIMUN</h2>
          <p className="text-sm text-slate-500 mt-2 font-mono">MEMULAKAN SISTEM...</p>
          <p className="text-xs text-teal-500/60 mt-1 italic">Himpunan Analisis Lindungan Intelijen Medan Udara Negara</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a1628] text-slate-100 overflow-hidden" data-testid="aegis-dashboard">
      {/* Header Bar */}
      <header className="h-14 bg-[#0f172a] border-b border-slate-800 flex items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-teal-500" />
            <span className="font-bold text-lg tracking-tight uppercase" style={{ fontFamily: 'Chivo, sans-serif' }}>
              PROJEK HALIMUN
            </span>
          </div>
          <span className="text-xs text-slate-400 border-l border-slate-700 pl-4 italic">
            "Perisai senyap angkasa memayungi negara"
          </span>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-xs">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            <span className="text-slate-400">SYSTEM ONLINE</span>
          </div>
          <div className="font-mono text-xs text-slate-400" data-testid="system-time">
            {formatTime(systemTime)}
          </div>
          <button 
            onClick={fetchData}
            className="p-2 hover:bg-slate-800 rounded transition-colors"
            data-testid="refresh-btn"
          >
            <RefreshCw className="w-4 h-4 text-slate-400" />
          </button>
        </div>
      </header>

      <div className="flex h-[calc(100vh-3.5rem)]">
        {/* Left Sidebar - Navigation */}
        <nav className="w-14 bg-[#0f172a] border-r border-slate-800 flex flex-col items-center py-4 gap-2">
          <NavButton 
            icon={<Map />} 
            active={activePanel === "map"} 
            onClick={() => setActivePanel("map")}
            tooltip="Battlefield Map"
            testId="nav-map"
          />
          <NavButton 
            icon={<Target />} 
            active={activePanel === "threats"} 
            onClick={() => setActivePanel("threats")}
            tooltip="Threat Assessment"
            testId="nav-threats"
          />
          <NavButton 
            icon={<MessageSquare />} 
            active={activePanel === "ai"} 
            onClick={() => setActivePanel("ai")}
            tooltip="AI Console"
            testId="nav-ai"
          />
          <NavButton 
            icon={<Zap />} 
            active={activePanel === "countermeasures"} 
            onClick={() => setActivePanel("countermeasures")}
            tooltip="Countermeasures"
            testId="nav-countermeasures"
          />
          <NavButton 
            icon={<Clock />} 
            active={activePanel === "timeline"} 
            onClick={() => setActivePanel("timeline")}
            tooltip="Timeline"
            testId="nav-timeline"
          />
          <NavButton 
            icon={<BarChart3 />} 
            active={activePanel === "metrics"} 
            onClick={() => setActivePanel("metrics")}
            tooltip="System Metrics"
            testId="nav-metrics"
          />
          <div className="flex-1"></div>
          <NavButton 
            icon={<Settings />} 
            active={false} 
            onClick={() => {}}
            tooltip="Settings"
            testId="nav-settings"
          />
        </nav>

        {/* Main Content Area */}
        <main className="flex-1 flex">
          {/* Map Area - Always visible */}
          <div className="flex-1 relative">
            <BattleMap 
              emitters={emitters} 
              onEmitterSelect={handleEmitterSelect}
              selectedEmitter={selectedEmitter}
            />
            
            {/* Overlay Metrics */}
            <div className="absolute top-4 left-4 flex gap-2">
              <MetricBadge 
                label="TRACKING" 
                value={metrics?.emitters_tracked || 0} 
                color="teal"
                testId="metric-tracking"
              />
              <MetricBadge 
                label="HOSTILE" 
                value={metrics?.hostile_count || 0} 
                color="red"
                testId="metric-hostile"
              />
              <MetricBadge 
                label="FRIENDLY" 
                value={metrics?.friendly_count || 0} 
                color="green"
                testId="metric-friendly"
              />
            </div>

            {/* Scenario Selector */}
            <div className="absolute top-4 right-4">
              <ScenarioSelector 
                onActivate={handleScenarioActivate}
                activeScenario={activeScenario}
              />
            </div>
          </div>

          {/* Right Panel - Dynamic Content */}
          <AnimatePresence mode="wait">
            <motion.aside
              key={activePanel}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.15 }}
              className="w-96 bg-[#0f172a] border-l border-slate-800 overflow-hidden flex flex-col"
            >
              {activePanel === "threats" && (
                <ThreatPanel 
                  threats={threats}
                  emitters={emitters}
                  onEmitterSelect={handleEmitterSelect}
                />
              )}
              {activePanel === "ai" && (
                <AIConsole selectedEmitter={selectedEmitter} />
              )}
              {activePanel === "countermeasures" && (
                <CountermeasurePanel selectedEmitter={selectedEmitter} />
              )}
              {activePanel === "timeline" && (
                <ThreatTimeline />
              )}
              {activePanel === "metrics" && (
                <MetricsPanel metrics={metrics} />
              )}
              {activePanel === "map" && (
                <ThreatPanel 
                  threats={threats}
                  emitters={emitters}
                  onEmitterSelect={handleEmitterSelect}
                />
              )}
              {activePanel === "analysis" && selectedEmitter && (
                <EmitterAnalysis 
                  emitter={selectedEmitter}
                  onClose={() => setActivePanel("threats")}
                />
              )}
            </motion.aside>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};

// Navigation Button Component
const NavButton = ({ icon, active, onClick, tooltip, testId }) => (
  <button
    onClick={onClick}
    className={`w-10 h-10 flex items-center justify-center rounded-sm transition-all duration-150 group relative
      ${active 
        ? 'bg-teal-500/20 text-teal-400 border border-teal-500/50' 
        : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800'
      }`}
    data-testid={testId}
    title={tooltip}
  >
    {React.cloneElement(icon, { className: 'w-5 h-5' })}
  </button>
);

// Metric Badge Component
const MetricBadge = ({ label, value, color, testId }) => {
  const colorClasses = {
    teal: 'bg-teal-500/20 text-teal-400 border-teal-500/50',
    red: 'bg-red-500/20 text-red-400 border-red-500/50',
    green: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50',
    amber: 'bg-amber-500/20 text-amber-400 border-amber-500/50',
    sky: 'bg-sky-500/20 text-sky-400 border-sky-500/50',
  };

  return (
    <div 
      className={`px-3 py-1.5 border rounded-sm ${colorClasses[color]} font-mono text-xs`}
      data-testid={testId}
    >
      <span className="text-slate-500 mr-2">{label}</span>
      <span className="font-bold">{value}</span>
    </div>
  );
};

// Emitter Analysis Panel
const EmitterAnalysis = ({ emitter, onClose }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchAnalysis = async () => {
    if (!emitter?.id) return;
    setLoading(true);
    try {
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/ai/analyze/${emitter.id}`
      );
      setAnalysis(response.data);
    } catch (error) {
      toast.error("Failed to fetch AI analysis");
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchAnalysis();
  }, [emitter]);

  return (
    <div className="h-full flex flex-col" data-testid="emitter-analysis-panel">
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            Emitter Analysis
          </h2>
          <button 
            onClick={onClose}
            className="text-slate-500 hover:text-slate-300 text-xs uppercase"
          >
            Close
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="hud-panel p-4">
          <h3 className="font-mono text-sky-400 text-sm mb-2">{emitter.name}</h3>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-slate-500">Type:</span>
              <span className="ml-2 text-slate-300">{emitter.emitter_type}</span>
            </div>
            <div>
              <span className="text-slate-500">Origin:</span>
              <span className="ml-2 text-slate-300">{emitter.origin}</span>
            </div>
            <div>
              <span className="text-slate-500">Platform:</span>
              <span className="ml-2 text-slate-300">{emitter.platform}</span>
            </div>
            <div>
              <span className="text-slate-500">Freq:</span>
              <span className="ml-2 font-mono text-slate-300">
                {emitter.frequency_min}-{emitter.frequency_max} MHz
              </span>
            </div>
          </div>
        </div>

        <div className="hud-panel p-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
            AI Analysis
          </h3>
          {loading ? (
            <div className="space-y-2">
              <div className="h-4 skeleton rounded"></div>
              <div className="h-4 skeleton rounded w-3/4"></div>
              <div className="h-4 skeleton rounded w-1/2"></div>
            </div>
          ) : analysis ? (
            <p className="text-sm text-slate-300 whitespace-pre-wrap">
              {analysis.analysis}
            </p>
          ) : (
            <p className="text-sm text-slate-500">No analysis available</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
