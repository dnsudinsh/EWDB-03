import React from "react";
import { motion } from "framer-motion";
import { Activity, Cpu, Clock, Zap, Database, Brain, Server, Gauge } from "lucide-react";
import { ScrollArea } from "./ui/scroll-area";

const MetricsPanel = ({ metrics }) => {
  const metricItems = [
    {
      label: "Emitters Tracked",
      value: metrics?.emitters_tracked || 0,
      unit: "",
      icon: <Activity className="w-4 h-4" />,
      color: "sky"
    },
    {
      label: "Classification Accuracy",
      value: ((metrics?.classification_accuracy || 0) * 100).toFixed(1),
      unit: "%",
      icon: <Brain className="w-4 h-4" />,
      color: "green"
    },
    {
      label: "Processing Latency",
      value: metrics?.processing_latency_ms || 0,
      unit: "ms",
      icon: <Cpu className="w-4 h-4" />,
      color: "amber"
    },
    {
      label: "Threat Assessment",
      value: metrics?.threat_assessment_ms || 0,
      unit: "ms",
      icon: <Zap className="w-4 h-4" />,
      color: "orange"
    },
    {
      label: "AI Response Time",
      value: metrics?.ai_response_ms || 0,
      unit: "ms",
      icon: <Server className="w-4 h-4" />,
      color: "purple"
    },
    {
      label: "System Uptime",
      value: metrics?.uptime_hours || 0,
      unit: "hrs",
      icon: <Clock className="w-4 h-4" />,
      color: "green"
    },
    {
      label: "Signals Processed (24h)",
      value: (metrics?.signals_processed_24h || 0).toLocaleString(),
      unit: "",
      icon: <Database className="w-4 h-4" />,
      color: "sky"
    }
  ];

  const colorClasses = {
    sky: { bg: 'bg-sky-500/20', text: 'text-sky-400', border: 'border-sky-500/50' },
    green: { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/50' },
    amber: { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/50' },
    orange: { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/50' },
    purple: { bg: 'bg-purple-500/20', text: 'text-purple-400', border: 'border-purple-500/50' },
    red: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/50' },
  };

  return (
    <div className="h-full flex flex-col" data-testid="metrics-panel">
      {/* Header */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-sky-500/20 rounded-sm">
            <Gauge className="w-4 h-4 text-sky-400" />
          </div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            System Metrics
          </h2>
        </div>
        <p className="text-xs text-slate-500 mt-2">
          Real-time performance monitoring
        </p>
      </div>

      {/* Metrics Grid */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-3">
          {metricItems.map((metric, index) => {
            const colors = colorClasses[metric.color] || colorClasses.sky;
            
            return (
              <motion.div
                key={metric.label}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`hud-panel p-4 border ${colors.border}`}
                data-testid={`metric-${index}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className={`p-1.5 rounded-sm ${colors.bg} ${colors.text}`}>
                      {metric.icon}
                    </div>
                    <span className="text-xs text-slate-400 uppercase tracking-wider">
                      {metric.label}
                    </span>
                  </div>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className={`text-2xl font-mono font-bold ${colors.text}`}>
                    {metric.value}
                  </span>
                  <span className="text-sm text-slate-500 font-mono">
                    {metric.unit}
                  </span>
                </div>
              </motion.div>
            );
          })}

          {/* System Status */}
          <div className="hud-panel p-4 border border-green-500/30">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-slate-400 uppercase tracking-wider">System Status</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <StatusItem label="Backend" status="online" />
              <StatusItem label="Database" status="online" />
              <StatusItem label="AI Engine" status="online" />
              <StatusItem label="WebSocket" status="standby" />
            </div>
          </div>

          {/* Performance Thresholds */}
          <div className="hud-panel p-4 border border-slate-700">
            <div className="text-xs text-slate-400 uppercase tracking-wider mb-3">
              Performance Targets
            </div>
            <div className="space-y-2">
              <PerformanceBar 
                label="Classification" 
                current={metrics?.classification_accuracy * 100 || 0} 
                target={95} 
              />
              <PerformanceBar 
                label="Latency" 
                current={100 - (metrics?.processing_latency_ms || 0) / 0.5} 
                target={100} 
                inverse
              />
              <PerformanceBar 
                label="Threat Response" 
                current={100 - (metrics?.threat_assessment_ms || 0) / 1} 
                target={100} 
                inverse
              />
            </div>
          </div>
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="p-4 border-t border-slate-800 text-xs text-slate-500 font-mono">
        Last updated: {metrics?.timestamp ? new Date(metrics.timestamp).toLocaleTimeString() : 'N/A'}
      </div>
    </div>
  );
};

// Status Item Component
const StatusItem = ({ label, status }) => {
  const statusColors = {
    online: 'text-green-400',
    offline: 'text-red-400',
    standby: 'text-amber-400',
    error: 'text-red-400'
  };

  return (
    <div className="flex items-center justify-between">
      <span className="text-slate-500">{label}</span>
      <span className={`uppercase font-mono ${statusColors[status]}`}>
        {status}
      </span>
    </div>
  );
};

// Performance Bar Component
const PerformanceBar = ({ label, current, target, inverse = false }) => {
  const percentage = Math.min(100, Math.max(0, current));
  const isGood = inverse ? percentage > 80 : percentage >= target;
  
  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-slate-500">{label}</span>
        <span className={`font-mono ${isGood ? 'text-green-400' : 'text-amber-400'}`}>
          {percentage.toFixed(0)}%
        </span>
      </div>
      <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div 
          className={`h-full transition-all duration-500 ${isGood ? 'bg-green-500' : 'bg-amber-500'}`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
};

export default MetricsPanel;
