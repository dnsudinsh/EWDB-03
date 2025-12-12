import React, { useState, useEffect } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { Zap, Shield, AlertTriangle, ChevronRight, Target, CheckCircle2 } from "lucide-react";
import { ScrollArea } from "./ui/scroll-area";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CountermeasurePanel = ({ selectedEmitter }) => {
  const [countermeasures, setCountermeasures] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCountermeasures();
  }, []);

  useEffect(() => {
    if (selectedEmitter) {
      fetchRecommendations(selectedEmitter.emitter_type);
    }
  }, [selectedEmitter]);

  const fetchCountermeasures = async () => {
    try {
      const response = await axios.get(`${API}/countermeasures`);
      setCountermeasures(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Failed to fetch countermeasures:", error);
      setLoading(false);
    }
  };

  const fetchRecommendations = async (threatType) => {
    try {
      const response = await axios.get(`${API}/countermeasures/recommend/${threatType}`);
      setRecommendations(response.data.recommendations || []);
    } catch (error) {
      console.error("Failed to fetch recommendations:", error);
    }
  };

  const handleDeploy = (cm) => {
    toast.success(`${cm.name} deployed`, {
      description: `Success probability: ${(cm.success_rate * 100).toFixed(0)}%`
    });
  };

  const getTypeColor = (type) => {
    const colors = {
      jamming: 'text-purple-400 bg-purple-500/20 border-purple-500/50',
      deception: 'text-sky-400 bg-sky-500/20 border-sky-500/50',
      chaff: 'text-amber-400 bg-amber-500/20 border-amber-500/50',
      flare: 'text-orange-400 bg-orange-500/20 border-orange-500/50',
      cyber: 'text-green-400 bg-green-500/20 border-green-500/50'
    };
    return colors[type] || 'text-slate-400 bg-slate-500/20 border-slate-500/50';
  };

  const getCostColor = (cost) => {
    const colors = {
      low: 'text-green-400',
      medium: 'text-amber-400',
      high: 'text-red-400'
    };
    return colors[cost] || 'text-slate-400';
  };

  return (
    <div className="h-full flex flex-col" data-testid="countermeasure-panel">
      {/* Header */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center gap-2 mb-2">
          <div className="p-1.5 bg-purple-500/20 rounded-sm">
            <Zap className="w-4 h-4 text-purple-400" />
          </div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            Countermeasures
          </h2>
        </div>
        <p className="text-xs text-slate-500">
          Electronic warfare response options
        </p>
      </div>

      {/* Recommendations Section */}
      {selectedEmitter && recommendations.length > 0 && (
        <div className="p-4 border-b border-slate-800 bg-sky-500/5">
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-4 h-4 text-sky-400" />
            <span className="text-xs text-sky-400 uppercase tracking-wider">
              Recommended for: {selectedEmitter.name}
            </span>
          </div>
          <div className="space-y-2">
            {recommendations.slice(0, 3).map((cm, index) => (
              <motion.div
                key={cm.id || index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-center justify-between p-2 bg-slate-800/50 rounded-sm border border-sky-500/30"
              >
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-sky-400" />
                  <span className="text-sm text-slate-200">{cm.name}</span>
                </div>
                <span className="text-xs font-mono text-green-400">
                  {(cm.success_rate * 100).toFixed(0)}%
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Countermeasures List */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-3">
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-24 skeleton rounded"></div>
              ))}
            </div>
          ) : (
            countermeasures.map((cm, index) => (
              <motion.div
                key={cm.id || index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="hud-panel p-4 group hover:border-purple-500/50 transition-colors"
                data-testid={`countermeasure-${index}`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs px-2 py-0.5 rounded-sm border uppercase ${getTypeColor(cm.technique_type)}`}>
                        {cm.technique_type}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-slate-200 group-hover:text-purple-400 transition-colors">
                      {cm.name}
                    </h3>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-lg font-mono font-bold text-green-400">
                      {(cm.success_rate * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-slate-500">success</div>
                  </div>
                </div>

                <p className="text-xs text-slate-400 mb-3 line-clamp-2">
                  {cm.description}
                </p>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 text-xs">
                    <span className="text-slate-500">
                      Cost: <span className={`font-mono uppercase ${getCostColor(cm.resource_cost)}`}>
                        {cm.resource_cost}
                      </span>
                    </span>
                  </div>
                  
                  <button
                    onClick={() => handleDeploy(cm)}
                    className="px-3 py-1 text-xs uppercase tracking-wider bg-purple-500/20 text-purple-400 border border-purple-500/50 hover:bg-purple-500 hover:text-white transition-colors"
                    data-testid={`deploy-cm-${index}`}
                  >
                    Deploy
                  </button>
                </div>

                {cm.side_effects && (
                  <div className="mt-3 pt-3 border-t border-slate-700/50">
                    <div className="flex items-start gap-2 text-xs">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                      <span className="text-amber-400/80">{cm.side_effects}</span>
                    </div>
                  </div>
                )}

                {cm.applicable_threats && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {cm.applicable_threats.map((threat, i) => (
                      <span 
                        key={i}
                        className="text-[10px] px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded"
                      >
                        {threat}
                      </span>
                    ))}
                  </div>
                )}
              </motion.div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Quick Deploy Panel */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/50">
        <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">Quick Deploy</div>
        <div className="flex gap-2">
          <button 
            onClick={() => toast.success("AN/SLQ-32 Mode 4 activated")}
            className="flex-1 py-2 text-xs uppercase tracking-wider bg-purple-500/20 text-purple-400 border border-purple-500/50 hover:bg-purple-500 hover:text-white transition-colors"
            data-testid="quick-deploy-jamming"
          >
            Jamming
          </button>
          <button 
            onClick={() => toast.success("Chaff deployed")}
            className="flex-1 py-2 text-xs uppercase tracking-wider bg-amber-500/20 text-amber-400 border border-amber-500/50 hover:bg-amber-500 hover:text-white transition-colors"
            data-testid="quick-deploy-chaff"
          >
            Chaff
          </button>
          <button 
            onClick={() => toast.success("Decoy launched")}
            className="flex-1 py-2 text-xs uppercase tracking-wider bg-sky-500/20 text-sky-400 border border-sky-500/50 hover:bg-sky-500 hover:text-white transition-colors"
            data-testid="quick-deploy-decoy"
          >
            Decoy
          </button>
        </div>
      </div>
    </div>
  );
};

export default CountermeasurePanel;
