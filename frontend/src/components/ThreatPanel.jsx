import React from "react";
import { motion } from "framer-motion";
import { AlertTriangle, Target, Radio, Shield, ChevronRight, Crosshair } from "lucide-react";
import { ScrollArea } from "./ui/scroll-area";

const ThreatPanel = ({ threats, emitters = [], onEmitterSelect }) => {
  const hostileEmitters = emitters.filter(e => e.affiliation === 'hostile');
  const friendlyEmitters = emitters.filter(e => e.affiliation === 'friendly');
  const assessments = threats?.assessments || [];

  const getThreatIcon = (type) => {
    switch (type) {
      case 'radar': return <Radio className="w-4 h-4" />;
      case 'missile': return <Target className="w-4 h-4" />;
      case 'communication': return <Radio className="w-4 h-4" />;
      default: return <AlertTriangle className="w-4 h-4" />;
    }
  };

  const getThreatColor = (level) => {
    switch (level) {
      case 'critical': return 'text-red-400 bg-red-500/20 border-red-500/50';
      case 'high': return 'text-orange-400 bg-orange-500/20 border-orange-500/50';
      case 'medium': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/50';
      case 'low': return 'text-green-400 bg-green-500/20 border-green-500/50';
      default: return 'text-slate-400 bg-slate-500/20 border-slate-500/50';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'text-red-400';
    if (score >= 0.6) return 'text-orange-400';
    if (score >= 0.4) return 'text-yellow-400';
    return 'text-green-400';
  };

  return (
    <div className="h-full flex flex-col" data-testid="threat-panel">
      {/* Header */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <Crosshair className="w-4 h-4 text-sky-400" />
            Threat Assessment
          </h2>
          <span className={`text-xs font-mono px-2 py-0.5 rounded ${
            threats?.critical_count > 0 ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
          }`}>
            {threats?.critical_count || 0} CRITICAL
          </span>
        </div>
        
        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-slate-800/50 p-2 rounded-sm border border-slate-700">
            <div className="text-xs text-slate-500 uppercase">Total</div>
            <div className="text-lg font-mono text-slate-100" data-testid="total-threats">
              {threats?.total_threats || 0}
            </div>
          </div>
          <div className="bg-red-500/10 p-2 rounded-sm border border-red-500/30">
            <div className="text-xs text-red-400 uppercase">Hostile</div>
            <div className="text-lg font-mono text-red-400" data-testid="hostile-count">
              {hostileEmitters.length}
            </div>
          </div>
          <div className="bg-sky-500/10 p-2 rounded-sm border border-sky-500/30">
            <div className="text-xs text-sky-400 uppercase">Friendly</div>
            <div className="text-lg font-mono text-sky-400" data-testid="friendly-count">
              {friendlyEmitters.length}
            </div>
          </div>
        </div>
      </div>

      {/* Threat List */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-2">
          {assessments.length > 0 ? (
            assessments.map((assessment, index) => (
              <motion.div
                key={assessment.emitter_id || index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="hud-panel p-3 cursor-pointer hover:border-sky-500/50 transition-colors group"
                onClick={() => {
                  const emitter = emitters.find(e => e.id === assessment.emitter_id || e.name === assessment.emitter_name);
                  if (emitter && onEmitterSelect) onEmitterSelect(emitter);
                }}
                data-testid={`threat-item-${index}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className={`p-1.5 rounded-sm ${
                      assessment.threat_score >= 0.8 ? 'bg-red-500/20 text-red-400' :
                      assessment.threat_score >= 0.6 ? 'bg-orange-500/20 text-orange-400' :
                      'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      <AlertTriangle className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-slate-200 group-hover:text-sky-400 transition-colors">
                        {assessment.emitter_name}
                      </div>
                      <div className="text-xs text-slate-500 font-mono">
                        Phase: {assessment.kill_chain_phase}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-mono font-bold ${getScoreColor(assessment.threat_score)}`}>
                      {(assessment.threat_score * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-slate-500">threat</div>
                  </div>
                </div>

                {assessment.time_to_impact && (
                  <div className="flex items-center gap-2 mb-2 text-xs">
                    <span className="text-red-400 font-mono animate-pulse">
                      TTI: {assessment.time_to_impact.toFixed(0)}s
                    </span>
                  </div>
                )}

                <div className="border-t border-slate-700/50 pt-2 mt-2">
                  <div className="text-xs text-slate-500 uppercase mb-1">Recommended Actions</div>
                  <div className="flex flex-wrap gap-1">
                    {assessment.recommended_actions?.slice(0, 2).map((action, i) => (
                      <span 
                        key={i}
                        className="text-xs px-2 py-0.5 bg-slate-800 text-slate-300 rounded-sm"
                      >
                        {action}
                      </span>
                    ))}
                  </div>
                </div>

                <ChevronRight className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600 group-hover:text-sky-400 transition-colors" />
              </motion.div>
            ))
          ) : (
            <div className="text-center py-8 text-slate-500">
              <Shield className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No active threats detected</p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Active Emitters List */}
      <div className="p-4 border-t border-slate-800">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
          Active Emitters
        </h3>
        <div className="space-y-1 max-h-32 overflow-y-auto">
          {emitters.slice(0, 5).map((emitter, index) => (
            <div 
              key={emitter.id || index}
              className="flex items-center justify-between text-xs py-1 px-2 hover:bg-slate-800/50 rounded-sm cursor-pointer"
              onClick={() => onEmitterSelect && onEmitterSelect(emitter)}
              data-testid={`emitter-list-item-${index}`}
            >
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  emitter.affiliation === 'hostile' ? 'bg-red-500' :
                  emitter.affiliation === 'friendly' ? 'bg-sky-500' :
                  'bg-amber-500'
                }`}></div>
                <span className="text-slate-300 truncate max-w-[180px]">{emitter.name}</span>
              </div>
              <span className={`font-mono ${getThreatColor(emitter.threat_level)} px-1.5 py-0.5 rounded text-[10px] uppercase border`}>
                {emitter.threat_level}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ThreatPanel;
