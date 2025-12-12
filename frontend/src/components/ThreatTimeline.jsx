import React, { useState, useEffect } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { Clock, AlertTriangle, Radio, Zap, Shield, Check } from "lucide-react";
import { ScrollArea } from "./ui/scroll-area";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ThreatTimeline = () => {
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTimeline();
    const interval = setInterval(fetchTimeline, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchTimeline = async () => {
    try {
      const response = await axios.get(`${API}/threats/timeline`);
      setTimeline(response.data.timeline || []);
      setLoading(false);
    } catch (error) {
      console.error("Failed to fetch timeline:", error);
      setLoading(false);
    }
  };

  const getEventIcon = (phase) => {
    switch (phase) {
      case 'detection': return <Radio className="w-3.5 h-3.5" />;
      case 'tracking': return <AlertTriangle className="w-3.5 h-3.5" />;
      case 'engagement': return <Zap className="w-3.5 h-3.5" />;
      case 'countermeasure': return <Shield className="w-3.5 h-3.5" />;
      case 'resolution': return <Check className="w-3.5 h-3.5" />;
      default: return <AlertTriangle className="w-3.5 h-3.5" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return {
        dot: 'bg-red-500',
        text: 'text-red-400',
        bg: 'bg-red-500/10',
        border: 'border-red-500/30'
      };
      case 'high': return {
        dot: 'bg-orange-500',
        text: 'text-orange-400',
        bg: 'bg-orange-500/10',
        border: 'border-orange-500/30'
      };
      case 'info': return {
        dot: 'bg-sky-500',
        text: 'text-sky-400',
        bg: 'bg-sky-500/10',
        border: 'border-sky-500/30'
      };
      case 'success': return {
        dot: 'bg-green-500',
        text: 'text-green-400',
        bg: 'bg-green-500/10',
        border: 'border-green-500/30'
      };
      default: return {
        dot: 'bg-slate-500',
        text: 'text-slate-400',
        bg: 'bg-slate-500/10',
        border: 'border-slate-500/30'
      };
    }
  };

  const formatTime = (timestamp, offset = 0) => {
    const date = new Date(timestamp);
    date.setMinutes(date.getMinutes() + offset);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  return (
    <div className="h-full flex flex-col" data-testid="threat-timeline">
      {/* Header */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center gap-2 mb-2">
          <div className="p-1.5 bg-amber-500/20 rounded-sm">
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            Threat Timeline
          </h2>
        </div>
        <p className="text-xs text-slate-500">
          Chronological event log
        </p>
      </div>

      {/* Timeline */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="flex gap-4">
                  <div className="w-12 h-4 skeleton rounded"></div>
                  <div className="flex-1 h-16 skeleton rounded"></div>
                </div>
              ))}
            </div>
          ) : (
            <div className="relative">
              {/* Timeline Line */}
              <div className="absolute left-[18px] top-2 bottom-2 w-px bg-slate-700"></div>

              <div className="space-y-4">
                {timeline.map((event, index) => {
                  const colors = getSeverityColor(event.severity);
                  
                  return (
                    <motion.div
                      key={event.id || index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="relative flex gap-4"
                      data-testid={`timeline-event-${index}`}
                    >
                      {/* Timeline Dot */}
                      <div className={`relative z-10 w-9 h-9 rounded-sm flex items-center justify-center ${colors.bg} ${colors.text} border ${colors.border}`}>
                        {getEventIcon(event.phase)}
                      </div>

                      {/* Event Content */}
                      <div className={`flex-1 p-3 rounded-sm ${colors.bg} border ${colors.border}`}>
                        <div className="flex items-start justify-between mb-1">
                          <span className={`text-xs uppercase tracking-wider font-mono ${colors.text}`}>
                            {event.phase}
                          </span>
                          <span className="text-xs text-slate-500 font-mono">
                            {formatTime(event.timestamp, event.offset_minutes || 0)}
                          </span>
                        </div>
                        <p className="text-sm text-slate-200">
                          {event.event}
                        </p>
                      </div>
                    </motion.div>
                  );
                })}

                {timeline.length === 0 && (
                  <div className="text-center py-8 text-slate-500">
                    <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No events recorded</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Phase Legend */}
      <div className="p-4 border-t border-slate-800">
        <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">Phase Legend</div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
            <span className="text-slate-400">Critical</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
            <span className="text-slate-400">High</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-sky-500 rounded-full"></div>
            <span className="text-slate-400">Info</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-slate-400">Resolved</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThreatTimeline;
