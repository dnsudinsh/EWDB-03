import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Shield, Radio, Target, Zap, AlertTriangle, Activity, 
  MessageSquare, Settings, Map, BarChart3, Clock, ChevronRight,
  Radar, Crosshair, Waves, Send, RefreshCw, Menu, X, 
  Maximize2, Minimize2, ChevronUp
} from "lucide-react";
import { toast } from "sonner";

// Import responsive utilities
import { 
  useResponsive, 
  useTouchOptimization, 
  usePerformanceMode,
  useNetworkAware
} from "../hooks/useResponsive";
import {
  ResponsiveLayout,
  MobileBottomNav,
  MobileDrawer,
  CollapsiblePanel,
  AdaptiveSidebar,
  ResponsiveMapContainer,
  DeviceIndicator
} from "../components/ResponsiveLayout";

// Import components
import BattleMap from "../components/BattleMap";
import ThreatPanel from "../components/ThreatPanel";
import AIConsole from "../components/AIConsole";
import MetricsPanel from "../components/MetricsPanel";
import ScenarioSelector from "../components/ScenarioSelector";
import CountermeasurePanel from "../components/CountermeasurePanel";
import ThreatTimeline from "../components/ThreatTimeline";

// Import responsive styles
import "../styles/responsive.css";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Dashboard = () => {
  // Responsive hooks
  const { deviceProfile, breakpoints, layout, windowSize } = useResponsive();
  const { isTouchDevice, getTouchTargetSize } = useTouchOptimization();
  const { performanceLevel, getPerformanceSettings, isLowBattery } = usePerformanceMode();
  const { isOnline, connectionQuality, getDataSyncMode } = useNetworkAware();

  // State
  const [emitters, setEmitters] = useState([]);
  const [threats, setThreats] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [activeScenario, setActiveScenario] = useState(null);
  const [selectedEmitter, setSelectedEmitter] = useState(null);
  const [activePanel, setActivePanel] = useState("threats");
  const [isLoading, setIsLoading] = useState(true);
  const [systemTime, setSystemTime] = useState(new Date());
  
  // Mobile-specific state
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [showDeviceInfo, setShowDeviceInfo] = useState(false);

  // Track if we've shown the connection error to avoid spam
  const [connectionErrorShown, setConnectionErrorShown] = useState(false);
  const [lastSuccessfulFetch, setLastSuccessfulFetch] = useState(null);

  // Performance-based settings
  const perfSettings = getPerformanceSettings();
  const syncMode = getDataSyncMode();

  // Adaptive refresh rate based on performance
  const getRefreshInterval = useCallback(() => {
    if (syncMode === 'offline') return null;
    if (syncMode === 'batch') return 30000;
    if (syncMode === 'throttled') return 10000;
    return perfSettings.refreshInterval;
  }, [syncMode, perfSettings]);

  // Fetch data with adaptive sampling
  const fetchData = useCallback(async () => {
    try {
      const [emittersRes, threatsRes, metricsRes] = await Promise.all([
        axios.get(`${API}/emitters`),
        axios.get(`${API}/threats/assess`),
        axios.get(`${API}/metrics`)
      ]);
      
      // Adaptive data sampling based on device capability
      let emitterData = emittersRes.data;
      if (perfSettings.maxDataPoints < emitterData.length) {
        const step = Math.ceil(emitterData.length / perfSettings.maxDataPoints);
        emitterData = emitterData.filter((_, i) => i % step === 0);
      }
      
      setEmitters(emitterData);
      setThreats(threatsRes.data);
      setMetrics(metricsRes.data);
      setIsLoading(false);
      
      // Reset error state on successful fetch
      if (connectionErrorShown) {
        setConnectionErrorShown(false);
        toast.success("Sambungan ke sistem HALIMUN dipulihkan");
      }
      setLastSuccessfulFetch(Date.now());
    } catch (error) {
      console.error("Error fetching data:", error);
      // Only show error toast once, not on every refresh failure
      // And only if we've been disconnected for more than 10 seconds
      if (isOnline && !connectionErrorShown && (!lastSuccessfulFetch || Date.now() - lastSuccessfulFetch > 10000)) {
        toast.error("Gagal menyambung ke sistem HALIMUN");
        setConnectionErrorShown(true);
      }
      setIsLoading(false);
    }
  }, [perfSettings.maxDataPoints, isOnline, connectionErrorShown, lastSuccessfulFetch]);

  useEffect(() => {
    fetchData();
    
    // System time update
    const timeInterval = setInterval(() => {
      setSystemTime(new Date());
    }, 1000);

    // Adaptive data refresh
    const refreshInterval = getRefreshInterval();
    let dataInterval;
    if (refreshInterval) {
      dataInterval = setInterval(fetchData, refreshInterval);
    }

    return () => {
      clearInterval(timeInterval);
      if (dataInterval) clearInterval(dataInterval);
    };
  }, [fetchData, getRefreshInterval]);

  const handleScenarioActivate = async (scenarioId) => {
    try {
      const response = await axios.post(`${API}/scenarios/${scenarioId}/activate`);
      setActiveScenario(response.data);
      toast.success(`Senario diaktifkan: ${response.data.emitters_loaded} pemancar dimuatkan`);
      fetchData();
    } catch (error) {
      toast.error("Gagal mengaktifkan senario");
    }
  };

  const handleEmitterSelect = (emitter) => {
    setSelectedEmitter(emitter);
    setActivePanel("analysis");
    if (breakpoints.isMobile) {
      setMobileDrawerOpen(true);
    }
  };

  const handlePanelChange = (panel) => {
    setActivePanel(panel);
    if (breakpoints.isMobile) {
      setMobileDrawerOpen(true);
    }
  };

  const formatTime = (date) => {
    return date.toISOString().replace('T', ' ').substring(0, 19) + 'Z';
  };

  // Navigation items
  const navItems = [
    { id: "map", icon: <Map size={20} />, label: "Peta", labelShort: "Peta" },
    { id: "threats", icon: <Target size={20} />, label: "Ancaman", labelShort: "Ancaman" },
    { id: "ai", icon: <MessageSquare size={20} />, label: "AI Konsol", labelShort: "AI" },
    { id: "countermeasures", icon: <Zap size={20} />, label: "Tindakan Balas", labelShort: "ECM" },
    { id: "timeline", icon: <Clock size={20} />, label: "Garis Masa", labelShort: "Masa" },
    { id: "metrics", icon: <BarChart3 size={20} />, label: "Metrik", labelShort: "Metrik" }
  ];

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a1628] flex items-center justify-center">
        <div className="text-center px-4">
          <div className="relative w-20 h-20 sm:w-24 sm:h-24 mx-auto mb-6">
            <div className="absolute inset-0 border-2 border-teal-500/30 rounded-full"></div>
            <div className="absolute inset-2 border-2 border-teal-500/50 rounded-full radar-sweep"></div>
            <div className="absolute inset-4 border-2 border-teal-500 rounded-full"></div>
            <Radar className="absolute inset-0 m-auto w-6 h-6 sm:w-8 sm:h-8 text-teal-500" />
          </div>
          <h2 className="text-lg sm:text-xl font-bold text-slate-100 tracking-wider uppercase">
            PROJEK HALIMUN
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-2 font-mono">
            MEMULAKAN SISTEM...
          </p>
          <p className="text-xs text-teal-500/60 mt-1 italic hidden sm:block">
            Himpunan Analisis Lindungan Intelijen Medan Udara Negara
          </p>
        </div>
      </div>
    );
  }

  // Render panel content
  const renderPanelContent = () => {
    switch (activePanel) {
      case "threats":
        return (
          <ThreatPanel 
            threats={threats}
            emitters={emitters}
            onEmitterSelect={handleEmitterSelect}
          />
        );
      case "ai":
        return <AIConsole selectedEmitter={selectedEmitter} />;
      case "countermeasures":
        return <CountermeasurePanel selectedEmitter={selectedEmitter} />;
      case "timeline":
        return <ThreatTimeline />;
      case "metrics":
        return <MetricsPanel metrics={metrics} />;
      case "analysis":
        return selectedEmitter ? (
          <EmitterAnalysis 
            emitter={selectedEmitter}
            onClose={() => {
              setActivePanel("threats");
              setMobileDrawerOpen(false);
            }}
          />
        ) : (
          <ThreatPanel 
            threats={threats}
            emitters={emitters}
            onEmitterSelect={handleEmitterSelect}
          />
        );
      default:
        return (
          <ThreatPanel 
            threats={threats}
            emitters={emitters}
            onEmitterSelect={handleEmitterSelect}
          />
        );
    }
  };

  return (
    <ResponsiveLayout>
      <div 
        className="dashboard-container" 
        data-testid="halimun-dashboard"
        style={{ 
          minHeight: '100vh',
          minHeight: '100dvh',
          background: '#0a1628'
        }}
      >
        {/* ============ HEADER ============ */}
        <header 
          className="dashboard-header"
          style={{
            height: breakpoints.isMobile ? '56px' : '64px',
            background: '#0f1f32',
            borderBottom: '1px solid #1e3a4f',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: `0 ${breakpoints.isMobile ? '12px' : '16px'}`,
            position: 'sticky',
            top: 0,
            zIndex: 100
          }}
        >
          {/* Logo & Title */}
          <div className="flex items-center gap-2 sm:gap-4">
            <Shield className="w-5 h-5 sm:w-6 sm:h-6 text-teal-500 flex-shrink-0" />
            <div>
              <span 
                className="font-bold tracking-tight uppercase text-slate-100"
                style={{ 
                  fontSize: breakpoints.isMobile ? '14px' : '18px',
                  fontFamily: 'Chivo, sans-serif'
                }}
              >
                PROJEK HALIMUN
              </span>
              {!breakpoints.isMobile && (
                <span className="text-xs text-slate-400 border-l border-slate-700 pl-3 ml-3 italic hidden lg:inline">
                  "Perisai senyap angkasa"
                </span>
              )}
            </div>
          </div>
          
          {/* Status & Controls */}
          <div className="flex items-center gap-2 sm:gap-4">
            {/* Connection Status */}
            <div className="flex items-center gap-1.5 text-xs">
              <div className={`w-2 h-2 rounded-full animate-pulse ${
                isOnline ? 'bg-emerald-500' : 'bg-red-500'
              }`}></div>
              <span className={`text-slate-400 hidden sm:inline ${
                !isOnline ? 'text-red-400' : ''
              }`}>
                {isOnline ? 'SISTEM AKTIF' : 'LUAR TALIAN'}
              </span>
            </div>
            
            {/* System Time */}
            <div 
              className="font-mono text-slate-400 hidden md:block"
              style={{ fontSize: '11px' }}
              data-testid="system-time"
            >
              {formatTime(systemTime)}
            </div>

            {/* Refresh Button */}
            <button 
              onClick={fetchData}
              className="touch-button"
              style={{
                padding: '8px',
                background: 'transparent',
                border: 'none',
                borderRadius: '4px',
                color: '#94a3b8',
                cursor: 'pointer'
              }}
              data-testid="refresh-btn"
              aria-label="Refresh data"
            >
              <RefreshCw className="w-4 h-4" />
            </button>

            {/* Menu button for tablet+ */}
            {!breakpoints.isMobile && breakpoints.isTablet && (
              <button 
                onClick={() => setMobileDrawerOpen(!mobileDrawerOpen)}
                className="touch-button"
                style={{
                  padding: '8px',
                  background: 'transparent',
                  border: 'none',
                  borderRadius: '4px',
                  color: '#94a3b8',
                  cursor: 'pointer'
                }}
              >
                <Menu className="w-5 h-5" />
              </button>
            )}
          </div>
        </header>

        {/* ============ MAIN CONTENT ============ */}
        <div 
          className="dashboard-main"
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: breakpoints.isMobile ? 'column' : 'row',
            overflow: 'hidden',
            height: breakpoints.isMobile 
              ? 'calc(100dvh - 56px - 64px)' // Header + bottom nav
              : 'calc(100dvh - 64px)'
          }}
        >
          {/* ============ DESKTOP/TABLET SIDEBAR NAV ============ */}
          {!breakpoints.isMobile && (
            <nav 
              className="dashboard-nav"
              style={{
                width: breakpoints.isTablet ? '56px' : '64px',
                background: '#0f1f32',
                borderRight: '1px solid #1e3a4f',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                padding: '16px 0',
                gap: '8px',
                flexShrink: 0
              }}
            >
              {navItems.map((item) => (
                <NavButton 
                  key={item.id}
                  icon={item.icon}
                  active={activePanel === item.id}
                  onClick={() => handlePanelChange(item.id)}
                  tooltip={item.label}
                  testId={`nav-${item.id}`}
                  compact={breakpoints.isTablet}
                />
              ))}
              
              <div className="flex-1"></div>
              
              {/* Dev info toggle */}
              <NavButton 
                icon={<Settings size={20} />}
                active={showDeviceInfo}
                onClick={() => setShowDeviceInfo(!showDeviceInfo)}
                tooltip="Info Peranti"
                testId="nav-settings"
                compact={breakpoints.isTablet}
              />
            </nav>
          )}

          {/* ============ MAP AREA ============ */}
          <ResponsiveMapContainer className="dashboard-map">
            <BattleMap 
              emitters={emitters} 
              onEmitterSelect={handleEmitterSelect}
              selectedEmitter={selectedEmitter}
              performanceMode={perfSettings.mapQuality}
            />
            
            {/* Overlay Metrics */}
            <div 
              className="map-controls map-controls-top-left"
              style={{
                display: 'flex',
                flexDirection: breakpoints.isMobile ? 'column' : 'row',
                gap: '8px'
              }}
            >
              <MetricBadge 
                label={breakpoints.isMobile ? "TRK" : "TRACKING"} 
                value={metrics?.emitters_tracked || 0} 
                color="teal"
                testId="metric-tracking"
              />
              <MetricBadge 
                label={breakpoints.isMobile ? "HST" : "HOSTILE"} 
                value={metrics?.hostile_count || 0} 
                color="red"
                testId="metric-hostile"
              />
              <MetricBadge 
                label={breakpoints.isMobile ? "FRD" : "FRIENDLY"} 
                value={metrics?.friendly_count || 0} 
                color="green"
                testId="metric-friendly"
              />
            </div>

            {/* Scenario Selector */}
            <div className="map-controls map-controls-top-right">
              <ScenarioSelector 
                onActivate={handleScenarioActivate}
                activeScenario={activeScenario}
                compact={breakpoints.isMobile}
              />
            </div>

            {/* Battery/Performance Warning */}
            {(isLowBattery || performanceLevel === 'low') && (
              <div 
                className="map-controls"
                style={{
                  bottom: breakpoints.isMobile ? '80px' : '16px',
                  left: '50%',
                  transform: 'translateX(-50%)'
                }}
              >
                <div style={{
                  background: 'rgba(234, 179, 8, 0.9)',
                  color: '#000',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontWeight: 'bold'
                }}>
                  {isLowBattery ? '⚠️ Bateri Rendah' : '⚠️ Mod Penjimatan'}
                </div>
              </div>
            )}
          </ResponsiveMapContainer>

          {/* ============ SIDEBAR/PANEL AREA ============ */}
          {!breakpoints.isMobile ? (
            <AdaptiveSidebar width={breakpoints.isCommandCenter ? 480 : 384}>
              <AnimatePresence mode="wait">
                <motion.div
                  key={activePanel}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.15 }}
                  style={{ height: '100%' }}
                >
                  {renderPanelContent()}
                </motion.div>
              </AnimatePresence>
            </AdaptiveSidebar>
          ) : (
            // Mobile: Use drawer for panels
            <MobileDrawer
              isOpen={mobileDrawerOpen}
              onClose={() => setMobileDrawerOpen(false)}
              position="bottom"
              title={navItems.find(n => n.id === activePanel)?.label || 'Panel'}
            >
              {renderPanelContent()}
            </MobileDrawer>
          )}
        </div>

        {/* ============ MOBILE BOTTOM NAV ============ */}
        <MobileBottomNav
          items={navItems}
          activeItem={activePanel}
          onItemClick={handlePanelChange}
        />

        {/* Dev Device Indicator */}
        <DeviceIndicator show={showDeviceInfo} />
      </div>
    </ResponsiveLayout>
  );
};

// ============ NAVIGATION BUTTON ============
const NavButton = ({ icon, active, onClick, tooltip, testId, compact = false }) => (
  <button
    onClick={onClick}
    className="touch-button"
    style={{
      width: compact ? '40px' : '44px',
      height: compact ? '40px' : '44px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      borderRadius: '4px',
      transition: 'all 0.15s ease',
      background: active ? 'rgba(20, 184, 166, 0.2)' : 'transparent',
      color: active ? '#14b8a6' : '#64748b',
      border: active ? '1px solid rgba(20, 184, 166, 0.5)' : '1px solid transparent',
      cursor: 'pointer'
    }}
    data-testid={testId}
    title={tooltip}
    aria-label={tooltip}
  >
    {React.cloneElement(icon, { 
      style: { width: compact ? '18px' : '20px', height: compact ? '18px' : '20px' }
    })}
  </button>
);

// ============ METRIC BADGE ============
const MetricBadge = ({ label, value, color, testId }) => {
  const colorClasses = {
    teal: { bg: 'rgba(20, 184, 166, 0.2)', text: '#14b8a6', border: 'rgba(20, 184, 166, 0.5)' },
    red: { bg: 'rgba(220, 38, 38, 0.2)', text: '#dc2626', border: 'rgba(220, 38, 38, 0.5)' },
    green: { bg: 'rgba(16, 185, 129, 0.2)', text: '#10b981', border: 'rgba(16, 185, 129, 0.5)' },
    amber: { bg: 'rgba(245, 158, 11, 0.2)', text: '#f59e0b', border: 'rgba(245, 158, 11, 0.5)' },
  };

  const colors = colorClasses[color] || colorClasses.teal;

  return (
    <div 
      className="metric-badge"
      style={{
        padding: '6px 10px',
        background: colors.bg,
        color: colors.text,
        border: `1px solid ${colors.border}`,
        borderRadius: '4px',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '11px',
        display: 'flex',
        alignItems: 'center',
        gap: '6px'
      }}
      data-testid={testId}
    >
      <span style={{ color: '#64748b' }}>{label}</span>
      <span style={{ fontWeight: 'bold' }}>{value}</span>
    </div>
  );
};

// ============ EMITTER ANALYSIS PANEL ============
const EmitterAnalysis = ({ emitter, onClose }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const { breakpoints } = useResponsive();

  const fetchAnalysis = useCallback(async () => {
    if (!emitter?.name) return;
    setLoading(true);
    try {
      const lookupId = encodeURIComponent(emitter.name);
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/ai/analyze/${lookupId}`
      );
      setAnalysis(response.data);
    } catch (error) {
      console.error("AI Analysis error:", error);
      toast.error("Gagal mendapatkan analisis AI");
    }
    setLoading(false);
  }, [emitter?.name]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  return (
    <div 
      style={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column' 
      }}
      data-testid="emitter-analysis-panel"
    >
      <div style={{
        padding: breakpoints.isMobile ? '12px' : '16px',
        borderBottom: '1px solid #1e3a4f',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <h2 style={{
          fontSize: breakpoints.isMobile ? '13px' : '14px',
          fontWeight: 'bold',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          color: '#cbd5e1',
          margin: 0
        }}>
          Analisis Pemancar
        </h2>
        <button 
          onClick={onClose}
          className="touch-button"
          style={{
            padding: '8px',
            background: 'transparent',
            border: 'none',
            color: '#64748b',
            cursor: 'pointer',
            fontSize: '12px',
            textTransform: 'uppercase'
          }}
        >
          Tutup
        </button>
      </div>

      <div style={{ 
        flex: 1, 
        overflowY: 'auto', 
        padding: breakpoints.isMobile ? '12px' : '16px'
      }}>
        {/* Emitter Details Card */}
        <div style={{
          background: '#0f1f32',
          border: '1px solid #1e3a4f',
          borderRadius: '4px',
          padding: breakpoints.isMobile ? '12px' : '16px',
          marginBottom: '16px'
        }}>
          <h3 style={{
            fontFamily: "'JetBrains Mono', monospace",
            color: '#14b8a6',
            fontSize: breakpoints.isMobile ? '13px' : '14px',
            marginBottom: '12px'
          }}>
            {emitter.name}
          </h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '8px',
            fontSize: '12px'
          }}>
            <div>
              <span style={{ color: '#64748b' }}>Jenis:</span>
              <span style={{ color: '#cbd5e1', marginLeft: '8px' }}>{emitter.emitter_type}</span>
            </div>
            <div>
              <span style={{ color: '#64748b' }}>Asal:</span>
              <span style={{ color: '#cbd5e1', marginLeft: '8px' }}>{emitter.origin}</span>
            </div>
            <div>
              <span style={{ color: '#64748b' }}>Platform:</span>
              <span style={{ color: '#cbd5e1', marginLeft: '8px' }}>{emitter.platform}</span>
            </div>
            <div>
              <span style={{ color: '#64748b' }}>Frek:</span>
              <span style={{ 
                color: '#cbd5e1', 
                marginLeft: '8px',
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: '11px'
              }}>
                {emitter.frequency_min}-{emitter.frequency_max} MHz
              </span>
            </div>
          </div>
        </div>

        {/* AI Analysis Card */}
        <div style={{
          background: '#0f1f32',
          border: '1px solid #1e3a4f',
          borderRadius: '4px',
          padding: breakpoints.isMobile ? '12px' : '16px'
        }}>
          <h3 style={{
            fontSize: '12px',
            fontWeight: 'bold',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: '#64748b',
            marginBottom: '12px'
          }}>
            Analisis AI
          </h3>
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {[1, 2, 3].map(i => (
                <div 
                  key={i}
                  className="skeleton" 
                  style={{ 
                    height: '16px', 
                    background: 'linear-gradient(90deg, #1e3a4f 25%, #2d4a5f 50%, #1e3a4f 75%)',
                    backgroundSize: '200% 100%',
                    animation: 'shimmer 1.5s infinite',
                    borderRadius: '4px',
                    width: i === 3 ? '60%' : '100%'
                  }}
                ></div>
              ))}
            </div>
          ) : analysis ? (
            <p style={{
              fontSize: '13px',
              color: '#cbd5e1',
              whiteSpace: 'pre-wrap',
              lineHeight: 1.6
            }}>
              {analysis.analysis}
            </p>
          ) : (
            <p style={{ fontSize: '13px', color: '#64748b' }}>
              Tiada analisis tersedia
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
