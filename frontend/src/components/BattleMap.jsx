import React, { useEffect, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, CircleMarker, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix for default marker icons in webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom marker icons
const createCustomIcon = (affiliation, threatLevel) => {
  const colors = {
    hostile: '#ef4444',
    friendly: '#0ea5e9',
    neutral: '#64748b',
    unknown: '#f59e0b'
  };
  
  const color = colors[affiliation] || colors.unknown;
  const size = threatLevel === 'critical' ? 14 : threatLevel === 'high' ? 12 : 10;
  
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        width: ${size}px;
        height: ${size}px;
        background: ${color};
        border: 2px solid ${color};
        border-radius: ${affiliation === 'hostile' ? '0' : '50%'};
        box-shadow: 0 0 10px ${color}, 0 0 20px ${color}40;
        transform: ${affiliation === 'hostile' ? 'rotate(45deg)' : 'none'};
      "></div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};

// Map bounds updater component
const MapUpdater = ({ emitters }) => {
  const map = useMap();
  
  useEffect(() => {
    if (emitters && emitters.length > 0) {
      const bounds = L.latLngBounds(
        emitters.map(e => [e.latitude, e.longitude])
      );
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 8 });
    }
  }, [emitters, map]);
  
  return null;
};

const BattleMap = ({ emitters = [], onEmitterSelect, selectedEmitter }) => {
  const mapRef = useRef(null);
  
  // Default center (Malaysia - Selat Melaka)
  const defaultCenter = [4.5, 108.0];
  const defaultZoom = 5;

  const getEmitterColor = (affiliation) => {
    const colors = {
      hostile: '#ef4444',
      friendly: '#0ea5e9',
      neutral: '#64748b',
      unknown: '#f59e0b'
    };
    return colors[affiliation] || colors.unknown;
  };

  const getThreatRadius = (threatLevel) => {
    const radii = {
      critical: 50000,
      high: 40000,
      medium: 30000,
      low: 20000
    };
    return radii[threatLevel] || 25000;
  };

  return (
    <div className="w-full h-full relative" data-testid="battle-map">
      <MapContainer
        ref={mapRef}
        center={defaultCenter}
        zoom={defaultZoom}
        className="w-full h-full"
        style={{ background: '#020617' }}
        zoomControl={false}
      >
        {/* Dark Map Tiles - CartoDB Dark Matter */}
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* Emitter Markers */}
        {emitters.map((emitter, index) => (
          <React.Fragment key={emitter.id || index}>
            {/* Threat Range Circle */}
            {emitter.affiliation === 'hostile' && (
              <CircleMarker
                center={[emitter.latitude, emitter.longitude]}
                radius={15}
                pathOptions={{
                  color: getEmitterColor(emitter.affiliation),
                  fillColor: getEmitterColor(emitter.affiliation),
                  fillOpacity: 0.1,
                  weight: 1,
                  dashArray: '4 4'
                }}
              />
            )}
            
            {/* Emitter Marker */}
            <Marker
              position={[emitter.latitude, emitter.longitude]}
              icon={createCustomIcon(emitter.affiliation, emitter.threat_level)}
              eventHandlers={{
                click: () => onEmitterSelect && onEmitterSelect(emitter)
              }}
            >
              <Popup className="aegis-popup">
                <div className="bg-slate-900 p-3 min-w-[200px] rounded border border-slate-700">
                  <div className="flex items-center gap-2 mb-2">
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: getEmitterColor(emitter.affiliation) }}
                    ></div>
                    <span className="font-bold text-slate-100 text-sm">{emitter.name}</span>
                  </div>
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Type:</span>
                      <span className="text-slate-300 font-mono">{emitter.emitter_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Origin:</span>
                      <span className="text-slate-300">{emitter.origin}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Platform:</span>
                      <span className="text-slate-300">{emitter.platform}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Frequency:</span>
                      <span className="text-slate-300 font-mono">
                        {emitter.frequency_min}-{emitter.frequency_max} MHz
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Threat:</span>
                      <span className={`font-bold uppercase ${
                        emitter.threat_level === 'critical' ? 'text-red-400' :
                        emitter.threat_level === 'high' ? 'text-orange-400' :
                        emitter.threat_level === 'medium' ? 'text-yellow-400' :
                        'text-green-400'
                      }`}>
                        {emitter.threat_level}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Position:</span>
                      <span className="text-slate-300 font-mono text-[10px]">
                        {emitter.latitude.toFixed(4)}°N, {emitter.longitude.toFixed(4)}°E
                      </span>
                    </div>
                  </div>
                  <button 
                    onClick={() => onEmitterSelect && onEmitterSelect(emitter)}
                    className="w-full mt-3 py-1.5 bg-sky-500/20 text-sky-400 text-xs uppercase tracking-wider border border-sky-500/50 hover:bg-sky-500/30 transition-colors"
                    data-testid={`analyze-emitter-${emitter.id || index}`}
                  >
                    Analyze
                  </button>
                </div>
              </Popup>
            </Marker>
          </React.Fragment>
        ))}

        <MapUpdater emitters={emitters} />
      </MapContainer>

      {/* Map Legend */}
      <div className="absolute bottom-4 left-4 bg-slate-900/90 border border-slate-700 p-3 rounded-sm text-xs z-[1000]" data-testid="map-legend">
        <div className="font-bold text-slate-400 uppercase tracking-wider mb-2">Legend</div>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rotate-45"></div>
            <span className="text-slate-300">Hostile</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-sky-500 rounded-full"></div>
            <span className="text-slate-300">Friendly</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-amber-500 rounded-full"></div>
            <span className="text-slate-300">Unknown</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-slate-500 rounded-full"></div>
            <span className="text-slate-300">Neutral</span>
          </div>
        </div>
      </div>

      {/* Coordinates Display */}
      <div className="absolute bottom-4 right-4 bg-slate-900/90 border border-slate-700 px-3 py-2 rounded-sm font-mono text-xs text-slate-400 z-[1000]">
        <span className="text-slate-500">EMITTERS:</span> {emitters.length}
      </div>
    </div>
  );
};

export default BattleMap;
