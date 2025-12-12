import React, { useState, useEffect } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { Play, ChevronDown, MapPin, AlertTriangle, Check } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Button } from "./ui/button";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ScenarioSelector = ({ onActivate, activeScenario }) => {
  const [scenarios, setScenarios] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    fetchScenarios();
  }, []);

  const fetchScenarios = async () => {
    try {
      const response = await axios.get(`${API}/scenarios`);
      setScenarios(response.data);
    } catch (error) {
      console.error("Failed to fetch scenarios:", error);
    }
  };

  const handleActivate = async (scenarioId) => {
    setLoading(true);
    try {
      await onActivate(scenarioId);
      setIsOpen(false);
    } catch (error) {
      toast.error("Failed to activate scenario");
    }
    setLoading(false);
  };

  return (
    <div data-testid="scenario-selector">
      <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
        <DropdownMenuTrigger asChild>
          <Button 
            variant="outline" 
            className="bg-slate-900/90 border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-slate-100 px-3 py-2"
            data-testid="scenario-dropdown-trigger"
          >
            <Play className="w-4 h-4 mr-2 text-sky-400" />
            <span className="text-xs uppercase tracking-wider">
              {activeScenario ? 'Scenario Active' : 'Load Scenario'}
            </span>
            <ChevronDown className="w-4 h-4 ml-2" />
          </Button>
        </DropdownMenuTrigger>
        
        <DropdownMenuContent 
          className="w-80 bg-slate-900 border-slate-700 p-2"
          align="end"
        >
          <div className="text-xs text-slate-500 uppercase tracking-wider px-2 py-1 mb-2">
            Demonstration Scenarios
          </div>
          
          {scenarios.map((scenario) => (
            <DropdownMenuItem
              key={scenario.id}
              onClick={() => handleActivate(scenario.id)}
              className="flex flex-col items-start p-3 cursor-pointer hover:bg-slate-800 rounded-sm focus:bg-slate-800 group"
              disabled={loading}
              data-testid={`scenario-item-${scenario.id}`}
            >
              <div className="flex items-center gap-2 w-full mb-1">
                <MapPin className="w-4 h-4 text-sky-400" />
                <span className="font-bold text-slate-200 text-sm group-hover:text-sky-400 transition-colors">
                  {scenario.name}
                </span>
                {activeScenario?.scenario_id === scenario.id && (
                  <Check className="w-4 h-4 text-green-400 ml-auto" />
                )}
              </div>
              
              <p className="text-xs text-slate-400 mb-2 line-clamp-2">
                {scenario.description}
              </p>
              
              <div className="flex items-center gap-3 text-xs">
                <span className="text-slate-500">
                  <span className="text-slate-400">Region:</span> {scenario.region}
                </span>
                <span className="text-slate-500">
                  <span className="text-slate-400">Emitters:</span> {scenario.emitters?.length || 0}
                </span>
              </div>
              
              {scenario.threat_summary && (
                <div className="mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded-sm w-full">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-red-400 flex-shrink-0 mt-0.5" />
                    <span className="text-xs text-red-300 line-clamp-2">
                      {scenario.threat_summary}
                    </span>
                  </div>
                </div>
              )}
            </DropdownMenuItem>
          ))}
          
          {scenarios.length === 0 && (
            <div className="text-center py-4 text-slate-500 text-sm">
              No scenarios available
            </div>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
      
      {/* Active Scenario Indicator */}
      <AnimatePresence>
        {activeScenario && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-2 px-3 py-2 bg-green-500/10 border border-green-500/30 rounded-sm"
            data-testid="active-scenario-indicator"
          >
            <div className="flex items-center gap-2 text-xs">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-green-400 font-mono uppercase">
                {activeScenario.emitters_loaded} emitters loaded
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ScenarioSelector;
