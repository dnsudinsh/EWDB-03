import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Menu, X, ChevronUp, ChevronDown, Maximize2, Minimize2,
  Sun, Moon, Eye, Smartphone, Tablet, Monitor, Tv
} from 'lucide-react';
import { useResponsive, useTouchOptimization, usePerformanceMode } from '../hooks/useResponsive';

// ============================================
// RESPONSIVE LAYOUT WRAPPER
// ============================================
export const ResponsiveLayout = ({ children, className = '' }) => {
  const { deviceProfile, breakpoints, layout } = useResponsive();
  const { isTouchDevice } = useTouchOptimization();
  const { performanceLevel } = usePerformanceMode();
  const [nightVisionMode, setNightVisionMode] = useState(false);
  const [briefingMode, setBriefingMode] = useState(false);
  const [gloveMode, setGloveMode] = useState(false);

  // Apply mode classes to body
  useEffect(() => {
    const body = document.body;
    body.classList.toggle('night-vision-mode', nightVisionMode);
    body.classList.toggle('briefing-mode', briefingMode);
    body.classList.toggle('glove-mode', gloveMode);
    body.classList.toggle('touch-device', isTouchDevice);
    body.classList.toggle('performance-low', performanceLevel === 'low');
    
    return () => {
      body.classList.remove('night-vision-mode', 'briefing-mode', 'glove-mode', 'touch-device', 'performance-low');
    };
  }, [nightVisionMode, briefingMode, gloveMode, isTouchDevice, performanceLevel]);

  const contextValue = {
    deviceProfile,
    breakpoints,
    layout,
    isTouchDevice,
    nightVisionMode,
    setNightVisionMode,
    briefingMode,
    setBriefingMode,
    gloveMode,
    setGloveMode
  };

  return (
    <ResponsiveContext.Provider value={contextValue}>
      <div 
        className={`responsive-layout ${deviceProfile} ${className}`}
        data-device={deviceProfile}
        data-touch={isTouchDevice}
        data-performance={performanceLevel}
      >
        {children}
      </div>
    </ResponsiveContext.Provider>
  );
};

// Context for responsive state
export const ResponsiveContext = React.createContext(null);
export const useResponsiveContext = () => React.useContext(ResponsiveContext);

// ============================================
// MOBILE BOTTOM NAVIGATION
// ============================================
export const MobileBottomNav = ({ items, activeItem, onItemClick }) => {
  const { breakpoints } = useResponsive();
  const { getTouchTargetSize } = useTouchOptimization();
  const touchSize = getTouchTargetSize('default');

  if (!breakpoints.isMobile) return null;

  return (
    <nav 
      className="mobile-bottom-nav"
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: '64px',
        background: 'var(--bg-paper)',
        borderTop: '1px solid var(--border-default)',
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'center',
        zIndex: 1000,
        paddingBottom: 'env(safe-area-inset-bottom)'
      }}
    >
      {items.slice(0, 5).map((item) => (
        <button
          key={item.id}
          onClick={() => onItemClick(item.id)}
          className="touch-button"
          style={{
            ...touchSize,
            flexDirection: 'column',
            gap: '4px',
            background: activeItem === item.id ? 'var(--accent-primary)' : 'transparent',
            color: activeItem === item.id ? 'var(--bg-default)' : 'var(--text-secondary)',
            border: 'none',
            borderRadius: '8px'
          }}
          data-testid={`mobile-nav-${item.id}`}
        >
          {item.icon}
          <span style={{ fontSize: 'var(--font-size-xs)' }}>{item.labelShort || item.label}</span>
        </button>
      ))}
    </nav>
  );
};

// ============================================
// MOBILE DRAWER
// ============================================
export const MobileDrawer = ({ 
  isOpen, 
  onClose, 
  children, 
  position = 'right',
  title 
}) => {
  const { breakpoints } = useResponsive();

  // Handle escape key
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose]);

  // Prevent body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  return (
    <div className={`mobile-drawer ${position} ${isOpen ? 'open' : ''}`}>
      <div 
        className="mobile-drawer-overlay"
        onClick={onClose}
        aria-hidden="true"
      />
      <motion.div 
        className="mobile-drawer-content"
        initial={false}
        animate={isOpen ? { x: 0 } : { x: position === 'left' ? '-100%' : '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
      >
        {position === 'bottom' && <div className="drawer-handle" />}
        
        <div className="drawer-header" style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: 'var(--space-md)',
          borderBottom: '1px solid var(--border-default)'
        }}>
          <h2 style={{ 
            fontSize: 'var(--font-size-lg)',
            fontWeight: 'bold',
            margin: 0 
          }}>
            {title}
          </h2>
          <button
            onClick={onClose}
            className="touch-button"
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-secondary)'
            }}
            aria-label="Close drawer"
          >
            <X size={24} />
          </button>
        </div>
        
        <div className="drawer-body" style={{ 
          padding: 'var(--space-md)',
          overflowY: 'auto',
          flex: 1
        }}>
          {children}
        </div>
      </motion.div>
    </div>
  );
};

// ============================================
// COLLAPSIBLE PANEL (FOR MOBILE)
// ============================================
export const CollapsiblePanel = ({ 
  title, 
  children, 
  defaultExpanded = false,
  icon,
  badge
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const { breakpoints } = useResponsive();

  // Auto-expand on larger screens
  useEffect(() => {
    if (!breakpoints.isMobile && !breakpoints.isTablet) {
      setIsExpanded(true);
    }
  }, [breakpoints]);

  return (
    <div className={`panel panel-collapsible ${isExpanded ? 'expanded' : ''}`}>
      <button
        className="panel-header touch-button"
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          width: '100%',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-sm)'
        }}
        aria-expanded={isExpanded}
      >
        {icon && <span className="panel-icon">{icon}</span>}
        <span style={{ 
          flex: 1, 
          textAlign: 'left',
          fontWeight: 'bold',
          fontSize: 'var(--font-size-sm)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em'
        }}>
          {title}
        </span>
        {badge && (
          <span className="metric-badge" style={{
            background: 'var(--accent-primary)',
            color: 'var(--bg-default)',
            padding: '2px 8px',
            borderRadius: '4px',
            fontSize: 'var(--font-size-xs)'
          }}>
            {badge}
          </span>
        )}
        {breakpoints.isMobile && (
          isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />
        )}
      </button>
      
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            className="panel-body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// ============================================
// ADAPTIVE SIDEBAR
// ============================================
export const AdaptiveSidebar = ({ 
  children, 
  width = 384,
  minWidth = 280,
  maxWidth = 480
}) => {
  const { breakpoints, layout } = useResponsive();
  const [drawerOpen, setDrawerOpen] = useState(false);

  // On mobile, render as drawer
  if (breakpoints.isMobile) {
    return (
      <>
        <button
          className="touch-button sidebar-toggle"
          onClick={() => setDrawerOpen(true)}
          style={{
            position: 'fixed',
            bottom: '80px',
            right: 'var(--space-md)',
            background: 'var(--accent-primary)',
            color: 'var(--bg-default)',
            borderRadius: '50%',
            width: '56px',
            height: '56px',
            border: 'none',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            zIndex: 999
          }}
          aria-label="Open sidebar"
        >
          <Menu size={24} />
        </button>
        
        <MobileDrawer
          isOpen={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          position="right"
          title="Panel"
        >
          {children}
        </MobileDrawer>
      </>
    );
  }

  // On larger screens, render as sidebar
  return (
    <aside 
      className="adaptive-sidebar"
      style={{
        width: breakpoints.isTablet ? '35%' : `${width}px`,
        minWidth: `${minWidth}px`,
        maxWidth: `${maxWidth}px`,
        height: '100%',
        borderLeft: '1px solid var(--border-default)',
        background: 'var(--bg-paper)',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      {children}
    </aside>
  );
};

// ============================================
// RESPONSIVE MAP CONTAINER
// ============================================
export const ResponsiveMapContainer = ({ 
  children, 
  onFullscreenToggle,
  className = ''
}) => {
  const { deviceProfile, breakpoints } = useResponsive();
  const { performanceLevel } = usePerformanceMode();
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen?.();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.();
      setIsFullscreen(false);
    }
    onFullscreenToggle?.(!isFullscreen);
  }, [isFullscreen, onFullscreenToggle]);

  // Get appropriate map height based on device
  const getMapHeight = () => {
    if (isFullscreen) return '100vh';
    if (breakpoints.isMobile) return 'var(--map-height-mobile)';
    if (breakpoints.isTablet) return 'var(--map-height-tablet)';
    if (breakpoints.isCommandCenter) return 'var(--map-height-command)';
    return 'var(--map-height-desktop)';
  };

  return (
    <div 
      className={`map-container ${deviceProfile} ${isFullscreen ? 'fullscreen' : ''} ${className}`}
      style={{
        position: 'relative',
        width: breakpoints.isMobile ? '100%' : undefined,
        height: getMapHeight(),
        flex: breakpoints.isMobile ? 'none' : 1
      }}
      data-performance={performanceLevel}
    >
      {children}
      
      {/* Fullscreen toggle - hidden on mobile */}
      {!breakpoints.isMobile && (
        <button
          className="touch-button map-fullscreen-btn"
          onClick={toggleFullscreen}
          style={{
            position: 'absolute',
            top: 'var(--space-md)',
            right: 'var(--space-md)',
            background: 'var(--bg-paper)',
            border: '1px solid var(--border-default)',
            borderRadius: '4px',
            zIndex: 1000,
            color: 'var(--text-primary)'
          }}
          aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
        >
          {isFullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
        </button>
      )}
    </div>
  );
};

// ============================================
// DEVICE INDICATOR (FOR DEVELOPMENT/DEMO)
// ============================================
export const DeviceIndicator = ({ show = false }) => {
  const { deviceProfile, windowSize, breakpoints } = useResponsive();
  const { isTouchDevice } = useTouchOptimization();
  const { performanceLevel, fps, connectionType } = usePerformanceMode();

  if (!show) return null;

  const getDeviceIcon = () => {
    if (breakpoints.isMobile) return <Smartphone size={16} />;
    if (breakpoints.isTablet) return <Tablet size={16} />;
    if (breakpoints.isCommandCenter) return <Tv size={16} />;
    return <Monitor size={16} />;
  };

  return (
    <div style={{
      position: 'fixed',
      bottom: breakpoints.isMobile ? '72px' : '8px',
      left: '8px',
      background: 'rgba(0,0,0,0.8)',
      color: '#fff',
      padding: '8px 12px',
      borderRadius: '4px',
      fontSize: '11px',
      fontFamily: 'monospace',
      zIndex: 9999,
      display: 'flex',
      flexDirection: 'column',
      gap: '4px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {getDeviceIcon()}
        <span style={{ textTransform: 'uppercase' }}>{deviceProfile}</span>
      </div>
      <div>{windowSize.width} × {windowSize.height}</div>
      <div>Touch: {isTouchDevice ? 'Yes' : 'No'}</div>
      <div>FPS: {fps} | {performanceLevel}</div>
      <div>Network: {connectionType}</div>
    </div>
  );
};

// ============================================
// RESPONSIVE SCENARIO CARD
// ============================================
export const ResponsiveScenarioCard = ({ 
  scenario, 
  isActive, 
  onClick,
  compact = false
}) => {
  const { breakpoints } = useResponsive();
  const { getTouchTargetSize } = useTouchOptimization();

  // Use compact mode on mobile
  const useCompact = compact || breakpoints.isMobile;

  return (
    <motion.div
      onClick={onClick}
      className="touch-button scenario-card"
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      style={{
        background: isActive ? 'var(--accent-primary)' : 'var(--bg-paper)',
        color: isActive ? 'var(--bg-default)' : 'var(--text-primary)',
        border: `1px solid ${isActive ? 'var(--accent-primary)' : 'var(--border-default)'}`,
        borderRadius: '8px',
        padding: useCompact ? 'var(--space-sm)' : 'var(--space-md)',
        cursor: 'pointer',
        width: '100%',
        textAlign: 'left',
        ...getTouchTargetSize('default')
      }}
      data-testid={`scenario-card-${scenario.id}`}
    >
      <div style={{
        fontWeight: 'bold',
        fontSize: useCompact ? 'var(--font-size-sm)' : 'var(--font-size-base)',
        marginBottom: useCompact ? '2px' : 'var(--space-xs)'
      }}>
        {scenario.name}
      </div>
      
      {!useCompact && (
        <>
          <div style={{
            fontSize: 'var(--font-size-xs)',
            opacity: 0.8,
            marginBottom: 'var(--space-xs)'
          }}>
            {scenario.name_bm}
          </div>
          <div style={{
            fontSize: 'var(--font-size-xs)',
            opacity: 0.7
          }}>
            {scenario.region}
          </div>
        </>
      )}
    </motion.div>
  );
};

export default ResponsiveLayout;
