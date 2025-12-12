import { useState, useEffect, useCallback, useMemo } from 'react';

// Military-specific breakpoints
export const BREAKPOINTS = {
  handheld: 480,
  mobile: 768,
  mobileCommand: 768,
  fieldTablet: 1024,
  commandLaptop: 1366,
  briefingHD: 1920,
  situationRoom: 3840,
  ultraWide: 5120
};

// Device capability profiles
export const DEVICE_PROFILES = {
  smartphone: {
    minWidth: 0,
    maxWidth: BREAKPOINTS.mobile,
    columns: 4,
    mapLayers: 2,
    dataPoints: 100,
    refreshRate: 5000,
    animations: 'reduced',
    touchMode: true,
    controls: 'minimal'
  },
  tablet: {
    minWidth: BREAKPOINTS.mobile,
    maxWidth: BREAKPOINTS.commandLaptop,
    columns: 8,
    mapLayers: 4,
    dataPoints: 500,
    refreshRate: 3000,
    animations: 'reduced',
    touchMode: true,
    controls: 'simplified'
  },
  laptop: {
    minWidth: BREAKPOINTS.commandLaptop,
    maxWidth: BREAKPOINTS.briefingHD,
    columns: 12,
    mapLayers: 6,
    dataPoints: 1000,
    refreshRate: 2000,
    animations: 'full',
    touchMode: false,
    controls: 'full'
  },
  desktop: {
    minWidth: BREAKPOINTS.briefingHD,
    maxWidth: BREAKPOINTS.situationRoom,
    columns: 12,
    mapLayers: 6,
    dataPoints: 5000,
    refreshRate: 1000,
    animations: 'full',
    touchMode: false,
    controls: 'full'
  },
  commandCenter: {
    minWidth: BREAKPOINTS.situationRoom,
    maxWidth: Infinity,
    columns: 16,
    mapLayers: 8,
    dataPoints: 10000,
    refreshRate: 500,
    animations: 'full',
    touchMode: false,
    controls: 'extended'
  }
};

// Main responsive hook
export const useResponsive = () => {
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 1920,
    height: typeof window !== 'undefined' ? window.innerHeight : 1080
  });
  
  const [orientation, setOrientation] = useState(
    typeof window !== 'undefined' 
      ? (window.innerWidth > window.innerHeight ? 'landscape' : 'portrait')
      : 'landscape'
  );

  const [devicePixelRatio, setDevicePixelRatio] = useState(
    typeof window !== 'undefined' ? window.devicePixelRatio : 1
  );

  useEffect(() => {
    let timeoutId;
    
    const handleResize = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        const width = window.innerWidth;
        const height = window.innerHeight;
        setWindowSize({ width, height });
        setOrientation(width > height ? 'landscape' : 'portrait');
        setDevicePixelRatio(window.devicePixelRatio);
      }, 100); // Debounce resize events
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleResize);
    
    return () => {
      clearTimeout(timeoutId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
    };
  }, []);

  // Determine current device profile
  const deviceProfile = useMemo(() => {
    const { width } = windowSize;
    
    if (width < BREAKPOINTS.mobile) return 'smartphone';
    if (width < BREAKPOINTS.commandLaptop) return 'tablet';
    if (width < BREAKPOINTS.briefingHD) return 'laptop';
    if (width < BREAKPOINTS.situationRoom) return 'desktop';
    return 'commandCenter';
  }, [windowSize]);

  // Get current profile settings
  const profile = useMemo(() => DEVICE_PROFILES[deviceProfile], [deviceProfile]);

  // Breakpoint checks
  const breakpoints = useMemo(() => ({
    isMobile: windowSize.width < BREAKPOINTS.mobile,
    isTablet: windowSize.width >= BREAKPOINTS.mobile && windowSize.width < BREAKPOINTS.commandLaptop,
    isLaptop: windowSize.width >= BREAKPOINTS.commandLaptop && windowSize.width < BREAKPOINTS.briefingHD,
    isDesktop: windowSize.width >= BREAKPOINTS.briefingHD && windowSize.width < BREAKPOINTS.situationRoom,
    isCommandCenter: windowSize.width >= BREAKPOINTS.situationRoom,
    isUltraWide: windowSize.width >= BREAKPOINTS.ultraWide,
    isPortrait: orientation === 'portrait',
    isLandscape: orientation === 'landscape',
    isHighDPI: devicePixelRatio > 1.5,
    isRetina: devicePixelRatio >= 2
  }), [windowSize, orientation, devicePixelRatio]);

  // Layout helpers
  const layout = useMemo(() => {
    const { width } = windowSize;
    
    if (width < BREAKPOINTS.mobile) {
      return {
        columns: 1,
        mapWidth: '100%',
        sidebarWidth: '100%',
        panelLayout: 'stacked',
        navPosition: 'bottom'
      };
    }
    
    if (width < BREAKPOINTS.commandLaptop) {
      return {
        columns: 2,
        mapWidth: '70%',
        sidebarWidth: '30%',
        panelLayout: 'side',
        navPosition: 'left'
      };
    }
    
    if (width < BREAKPOINTS.situationRoom) {
      return {
        columns: 3,
        mapWidth: '60%',
        sidebarWidth: '25%',
        controlsWidth: '15%',
        panelLayout: 'three-column',
        navPosition: 'left'
      };
    }
    
    return {
      columns: 4,
      mapWidth: '50%',
      sidebarWidth: '20%',
      controlsWidth: '15%',
      monitorWidth: '15%',
      panelLayout: 'four-column',
      navPosition: 'left'
    };
  }, [windowSize]);

  return {
    windowSize,
    orientation,
    devicePixelRatio,
    deviceProfile,
    profile,
    breakpoints,
    layout,
    // Utility functions
    isMinWidth: useCallback((minWidth) => windowSize.width >= minWidth, [windowSize.width]),
    isMaxWidth: useCallback((maxWidth) => windowSize.width < maxWidth, [windowSize.width]),
    isBetween: useCallback((min, max) => windowSize.width >= min && windowSize.width < max, [windowSize.width])
  };
};

// Touch optimization hook
export const useTouchOptimization = () => {
  const [isTouchDevice, setIsTouchDevice] = useState(false);
  const [lastTouchTime, setLastTouchTime] = useState(0);
  const [isLongPress, setIsLongPress] = useState(false);

  useEffect(() => {
    // Detect touch capability
    const hasTouch = 'ontouchstart' in window || 
                     navigator.maxTouchPoints > 0 || 
                     navigator.msMaxTouchPoints > 0;
    setIsTouchDevice(hasTouch);

    // Track touch events for hybrid detection
    const handleTouch = () => setLastTouchTime(Date.now());
    window.addEventListener('touchstart', handleTouch, { passive: true });
    
    return () => window.removeEventListener('touchstart', handleTouch);
  }, []);

  // Long press detection
  const handleLongPressStart = useCallback((callback, duration = 800) => {
    let timer;
    
    const start = (e) => {
      timer = setTimeout(() => {
        setIsLongPress(true);
        callback(e);
      }, duration);
    };
    
    const cancel = () => {
      clearTimeout(timer);
      setIsLongPress(false);
    };
    
    return { onTouchStart: start, onTouchEnd: cancel, onTouchMove: cancel };
  }, []);

  // Get appropriate touch target size
  const getTouchTargetSize = useCallback((type = 'default') => {
    const sizes = {
      small: { minWidth: 36, minHeight: 36, padding: 8 },
      default: { minWidth: 44, minHeight: 44, padding: 12 },
      large: { minWidth: 56, minHeight: 56, padding: 16 },
      gloveMode: { minWidth: 64, minHeight: 64, padding: 20 }
    };
    return sizes[type] || sizes.default;
  }, []);

  return {
    isTouchDevice,
    isRecentlyTouched: Date.now() - lastTouchTime < 1000,
    isLongPress,
    handleLongPressStart,
    getTouchTargetSize
  };
};

// Performance mode hook
export const usePerformanceMode = () => {
  const [performanceLevel, setPerformanceLevel] = useState('high');
  const [fps, setFps] = useState(60);
  const [batteryLevel, setBatteryLevel] = useState(100);
  const [isLowBattery, setIsLowBattery] = useState(false);
  const [connectionType, setConnectionType] = useState('4g');

  useEffect(() => {
    // Monitor FPS
    let frameCount = 0;
    let lastTime = performance.now();
    let animationId;

    const measureFPS = () => {
      frameCount++;
      const currentTime = performance.now();
      
      if (currentTime - lastTime >= 1000) {
        setFps(frameCount);
        frameCount = 0;
        lastTime = currentTime;
        
        // Adjust performance level based on FPS
        if (frameCount < 20) setPerformanceLevel('low');
        else if (frameCount < 40) setPerformanceLevel('medium');
        else setPerformanceLevel('high');
      }
      
      animationId = requestAnimationFrame(measureFPS);
    };

    animationId = requestAnimationFrame(measureFPS);

    // Monitor battery
    if ('getBattery' in navigator) {
      navigator.getBattery().then(battery => {
        setBatteryLevel(battery.level * 100);
        setIsLowBattery(battery.level < 0.2);
        
        battery.addEventListener('levelchange', () => {
          setBatteryLevel(battery.level * 100);
          setIsLowBattery(battery.level < 0.2);
        });
      });
    }

    // Monitor connection
    if ('connection' in navigator) {
      const conn = navigator.connection;
      setConnectionType(conn.effectiveType || '4g');
      
      conn.addEventListener('change', () => {
        setConnectionType(conn.effectiveType || '4g');
      });
    }

    return () => cancelAnimationFrame(animationId);
  }, []);

  // Get performance settings based on current conditions
  const getPerformanceSettings = useCallback(() => {
    const isConstrained = isLowBattery || connectionType === 'slow-2g' || connectionType === '2g';
    
    if (isConstrained || performanceLevel === 'low') {
      return {
        mapQuality: 'low',
        animations: 'none',
        maxDataPoints: 100,
        refreshInterval: 10000,
        lazyLoadThreshold: 500,
        enableParticles: false,
        enableShadows: false
      };
    }
    
    if (performanceLevel === 'medium') {
      return {
        mapQuality: 'medium',
        animations: 'reduced',
        maxDataPoints: 500,
        refreshInterval: 5000,
        lazyLoadThreshold: 1000,
        enableParticles: false,
        enableShadows: true
      };
    }
    
    return {
      mapQuality: 'high',
      animations: 'full',
      maxDataPoints: 5000,
      refreshInterval: 2000,
      lazyLoadThreshold: 2000,
      enableParticles: true,
      enableShadows: true
    };
  }, [performanceLevel, isLowBattery, connectionType]);

  return {
    performanceLevel,
    fps,
    batteryLevel,
    isLowBattery,
    connectionType,
    isSlowConnection: ['slow-2g', '2g', '3g'].includes(connectionType),
    getPerformanceSettings
  };
};

// Network-aware features hook
export const useNetworkAware = () => {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );
  const [connectionQuality, setConnectionQuality] = useState('good');

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Monitor connection quality
    if ('connection' in navigator) {
      const updateQuality = () => {
        const conn = navigator.connection;
        const downlink = conn.downlink || 10;
        const rtt = conn.rtt || 0;
        
        if (downlink < 1 || rtt > 500) setConnectionQuality('poor');
        else if (downlink < 5 || rtt > 200) setConnectionQuality('moderate');
        else setConnectionQuality('good');
      };
      
      updateQuality();
      navigator.connection.addEventListener('change', updateQuality);
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const getDataSyncMode = useCallback(() => {
    if (!isOnline) return 'offline';
    if (connectionQuality === 'poor') return 'batch';
    if (connectionQuality === 'moderate') return 'throttled';
    return 'realtime';
  }, [isOnline, connectionQuality]);

  return {
    isOnline,
    connectionQuality,
    getDataSyncMode,
    shouldDeferHeavyOperations: connectionQuality !== 'good'
  };
};

export default useResponsive;
