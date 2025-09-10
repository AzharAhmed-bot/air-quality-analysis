import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useSelector } from 'react-redux';

// Type definitions
type SensorDataValue = {
  value_type: string;
  value: string;
};

type LocationType = {
  latitude: string;
  longitude: string;
  country?: string;
  city?: string;
};

type SensorItem = {
  id: string | number;
  location: LocationType;
  sensordatavalues?: SensorDataValue[];
  timestamp: string;
};

type LiveDataResults = {
  results: SensorItem[];
};

type RootState = {
  liveData: {
    liveData: LiveDataResults | null;
  };
};

type TransformedSensor = {
  id: string | number;
  location: {
    lat: number;
    lng: number;
    country?: string;
    city?: string;
  };
  values: {
    P0: number;
    P2: number;
    P1: number;
    temperature: number;
    humidity: number;
  };
  timestamp: string;
};

// Add Leaflet types to window
declare global {
  interface Window {
    L: any;
  }
}

const AirQualityMap: React.FC = () => {
  const liveData = useSelector((state: RootState) => state.liveData.liveData);

  const [selectedMetric, setSelectedMetric] = useState<'P0' | 'P2' | 'P1'>('P2');
  const [loading, setLoading] = useState(true);
  const mapRef = useRef<HTMLDivElement | null>(null);
  const leafletMapRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);

  // ✅ Only keep sensors from Kenya
  const transformedData: TransformedSensor[] = useMemo(() => {
    if (!liveData?.results) return [];

    return liveData.results
      .filter(item => item.location?.latitude && item.location?.longitude)
      .filter(item => item.location?.country?.toLowerCase() === "kenya")
      .map(item => {
        const values: Record<string, number> = {};
        item.sensordatavalues?.forEach(sensor => {
          values[sensor.value_type] = parseFloat(sensor.value) || 0;
        });

        return {
          id: item.id,
          location: {
            lat: parseFloat(item.location.latitude),
            lng: parseFloat(item.location.longitude),
            country: item.location.country,
            city: item.location.city || 'Unknown Location'
          },
          values: {
            P0: values.P0 || 0,
            P2: values.P2 || 0,
            P1: values.P1 || 0,
            temperature: values.temperature || 0,
            humidity: values.humidity || 0
          },
          timestamp: item.timestamp
        };
      });
  }, [liveData]);

  // Color coding for air quality levels
  const getAirQualityColor = (value: number, metric: string) => {
    let thresholds: number[];
    switch (metric) {
      case 'P2': thresholds = [12, 35, 55, 150]; break;
      case 'P1': thresholds = [20, 50, 100, 200]; break;
      case 'P0': thresholds = [10, 25, 50, 100]; break;
      default: thresholds = [12, 35, 55, 150];
    }
    if (value <= thresholds[0]) return '#4ade80';
    if (value <= thresholds[1]) return '#fbbf24';
    if (value <= thresholds[2]) return '#fb923c';
    if (value <= thresholds[3]) return '#ef4444';
    return '#7c2d12';
  };

  const getAirQualityLabel = (value: number, metric: string) => {
    let thresholds: number[];
    switch (metric) {
      case 'P2': thresholds = [12, 35, 55, 150]; break;
      case 'P1': thresholds = [20, 50, 100, 200]; break;
      case 'P0': thresholds = [10, 25, 50, 100]; break;
      default: thresholds = [12, 35, 55, 150];
    }
    if (value <= thresholds[0]) return 'Good';
    if (value <= thresholds[1]) return 'Moderate';
    if (value <= thresholds[2]) return 'Unhealthy for Sensitive';
    if (value <= thresholds[3]) return 'Unhealthy';
    return 'Very Unhealthy';
  };

  // Initialize Leaflet map
  useEffect(() => {
    if (!mapRef.current || leafletMapRef.current) return;

    const loadLeaflet = async () => {
      if (!document.querySelector('link[href*="leaflet"]')) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css';
        document.head.appendChild(link);
      }

      if (!window.L) {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js';
        document.head.appendChild(script);
        script.onload = () => initializeMap();
      } else {
        initializeMap();
      }
    };

    const initializeMap = () => {
      if (!window.L || leafletMapRef.current) return;

      // ✅ Default center on Kenya
      const map = window.L.map(mapRef.current, {
        center: [0.0236, 37.9062], // Kenya lat/lng
        zoom: 6,
        zoomControl: true,
        scrollWheelZoom: true
      });

      window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
      }).addTo(map);

      leafletMapRef.current = map;
      setLoading(false);
    };

    loadLeaflet();

    return () => {
      if (leafletMapRef.current) {
        leafletMapRef.current.remove();
        leafletMapRef.current = null;
      }
    };
  }, []);

  // Update markers when data or metric changes
  useEffect(() => {
    if (!leafletMapRef.current || !transformedData.length) return;

    const map = leafletMapRef.current;

    markersRef.current.forEach(marker => map.removeLayer(marker));
    markersRef.current = [];

    transformedData.forEach(sensor => {
      const value = sensor.values[selectedMetric] || 0;
      const color = getAirQualityColor(value, selectedMetric);
      const label = getAirQualityLabel(value, selectedMetric);

      const markerHtml = `
        <div style="
          width: 40px; height: 40px;
          background-color: ${color};
          border: 3px solid white;
          border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          color: white; font-weight: bold; font-size: 12px;
          box-shadow: 0 2px 6px rgba(0,0,0,0.3); cursor: pointer;
        ">
          ${Math.round(value)}
        </div>
      `;

      const customIcon = window.L.divIcon({
        html: markerHtml,
        className: 'custom-air-quality-marker',
        iconSize: [40, 40],
        iconAnchor: [20, 20]
      });

      const popupContent = `
        <div style="min-width: 200px; font-family: system-ui;">
          <h3 style="margin: 0 0 10px 0; color: #333; font-size: 16px; font-weight: bold;">
            ${sensor.location.city}
          </h3>
          <div style="color: #666; font-size: 12px; margin-bottom: 10px;">
            ${sensor.location.country}
          </div>
          <div style="display: flex; flex-direction: column; gap: 6px; font-size: 14px;">
            <div style="display: flex; justify-content: space-between;">
              <span>PM1 (P0):</span><strong>${sensor.values.P0.toFixed(1)} μg/m³</strong>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span>PM2.5 (P2):</span><strong>${sensor.values.P2.toFixed(1)} μg/m³</strong>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span>PM10 (P1):</span><strong>${sensor.values.P1.toFixed(1)} μg/m³</strong>
            </div>
            ${sensor.values.temperature ? `<div style="display: flex; justify-content: space-between;">
              <span>Temperature:</span><strong>${sensor.values.temperature.toFixed(1)}°C</strong>
            </div>` : ''}
            ${sensor.values.humidity ? `<div style="display: flex; justify-content: space-between;">
              <span>Humidity:</span><strong>${sensor.values.humidity.toFixed(1)}%</strong>
            </div>` : ''}
          </div>
          <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>Air Quality:</span>
              <span style="background-color: ${color}; color: white;
                padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                ${label}
              </span>
            </div>
          </div>
          <div style="margin-top: 8px; color: #888; font-size: 11px;">
            Last updated: ${new Date(sensor.timestamp).toLocaleString()}
          </div>
        </div>
      `;

      const marker = window.L.marker([sensor.location.lat, sensor.location.lng], {
        icon: customIcon
      }).addTo(map);

      marker.bindPopup(popupContent, { maxWidth: 300, className: 'air-quality-popup' });

      markersRef.current.push(marker);
    });

    if (transformedData.length > 0) {
      const group = new window.L.featureGroup(markersRef.current);
      map.fitBounds(group.getBounds().pad(0.2));
    }
  }, [transformedData, selectedMetric]);

  if (loading) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-gray-100">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span>Loading air quality data...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-screen relative">
      {/* Header Controls */}
      <div className="absolute top-4 left-4 z-[1000] bg-white rounded-lg shadow-lg p-4">
        <h1 className="text-xl font-bold mb-3 text-gray-800">Air Quality Monitor (Kenya)</h1>
        <div className="flex space-x-2 mb-2">
          {(['P0', 'P2', 'P1'] as const).map((metric) => (
            <button
              key={metric}
              onClick={() => setSelectedMetric(metric)}
              className={`px-3 py-2 rounded text-sm font-medium transition-colors ${
                selectedMetric === metric 
                  ? 'bg-blue-500 text-white shadow-md' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {metric === 'P0' ? 'PM1' : metric === 'P2' ? 'PM2.5' : 'PM10'}
            </button>
          ))}
        </div>
        <div className="text-sm text-gray-600">
          Showing {transformedData.length} active sensors
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-white rounded-lg shadow-lg p-4">
        <h3 className="text-sm font-semibold mb-3 text-gray-800">Air Quality Index</h3>
        <div className="space-y-2 text-xs">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-400 rounded"></div>
            <span>Good</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-yellow-400 rounded"></div>
            <span>Moderate</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-orange-400 rounded"></div>
            <span>Unhealthy for Sensitive</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-500 rounded"></div>
            <span>Unhealthy</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4" style={{ backgroundColor: '#7c2d12' }}></div>
            <span>Very Unhealthy</span>
          </div>
        </div>
      </div>

      {/* Map */}
      <div ref={mapRef} className="w-full h-full" />

      {/* Custom marker popup styling */}
      <style>{`
        .custom-air-quality-marker {
          background: transparent !important;
          border: none !important;
        }
        .air-quality-popup .leaflet-popup-content-wrapper {
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .air-quality-popup .leaflet-popup-content {
          margin: 16px;
        }
      `}</style>
    </div>
  );
};

export default AirQualityMap;
