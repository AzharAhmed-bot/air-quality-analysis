"use client";

import {
  APIProvider,
  Map,
  AdvancedMarker,
  useMap,
} from "@vis.gl/react-google-maps";
import { MarkerClusterer } from "@googlemaps/markerclusterer";
import type { Marker } from "@googlemaps/markerclusterer";
import { useEffect, useState, useRef } from "react";
import { 
  Radio, 
  MapPin, 
  Clock, 
  Building2, 
  Hash, 
  Cpu,
  Activity,
  ChevronRight
} from "lucide-react";

// ----------------- Types -----------------
export interface SensorDataValue {
  id: number;
  value: string;
  value_type: string;
}

export interface Location {
  id: number;
  latitude: string;
  longitude: string;
}

export interface SensorType {
  id: number;
  name: string;
  manufacturer: string;
}

export interface Sensor {
  id: number;
  pin: string;
  sensor_type: SensorType;
}

export interface LiveData {
  id: number;
  sampling_rate: number | null;
  timestamp: string;
  sensordatavalues: SensorDataValue[];
  location: Location;
  sensor: Sensor;
}

// Helper function to get sensor status color based on data
const getSensorStatusColor = (sensorData: SensorDataValue[]) => {
  const hasData = sensorData.length > 0;
  return hasData ? "text-emerald-500" : "text-gray-400";
};

const getSensorBgColor = (sensorData: SensorDataValue[]) => {
  const hasData = sensorData.length > 0;
  return hasData ? "bg-emerald-50 border-emerald-200" : "bg-gray-50 border-gray-200";
};

// ----------------- Component -----------------
export default function AirQualityMap({ liveData }: { liveData: LiveData[] }) {
  const [selectedSensor, setSelectedSensor] = useState<LiveData | null>(null);

  return (
    <APIProvider apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY}>
      <div className="flex w-full h-[700px] bg-white rounded-2xl overflow-hidden shadow-xl border border-gray-100">
        {/* LEFT PANEL */}
        <div className="w-96 bg-gradient-to-b from-gray-50 to-white border-r border-gray-200 flex flex-col">
          {/* Header */}
          <div className="p-6 border-b border-gray-200 bg-white">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-blue-100 rounded-xl">
                <Radio className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Air Quality Monitor</h1>
                <p className="text-sm text-gray-500">{liveData.length} sensors active</p>
              </div>
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 p-6 overflow-y-auto">
            {!selectedSensor ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center max-w-sm">
                  <div className="mx-auto w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                    <MapPin className="w-10 h-10 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    Select a Sensor
                  </h3>
                  <p className="text-gray-500 text-sm leading-relaxed">
                    Click on any sensor marker on the map to view detailed information about its readings and status.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Sensor Header */}
                <div className={`p-4 rounded-2xl border-2 ${getSensorBgColor(selectedSensor.sensordatavalues)}`}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`p-2 rounded-xl ${getSensorStatusColor(selectedSensor.sensordatavalues)} bg-white shadow-sm`}>
                      <Activity className="w-5 h-5" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">
                        Sensor #{selectedSensor.sensor.id}
                      </h2>
                      <p className="text-sm text-gray-500">
                        {selectedSensor.sensor.sensor_type.name}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Sensor Details */}
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Cpu className="w-5 h-5 text-blue-600" />
                    Device Information
                  </h3>
                  
                  <div className="space-y-3">
                    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                      <Hash className="w-4 h-4 text-gray-400" />
                      <div>
                        <p className="text-sm font-medium text-gray-700">Device ID</p>
                        <p className="text-gray-900 font-mono">{selectedSensor.sensor.id}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                      <Building2 className="w-4 h-4 text-gray-400" />
                      <div>
                        <p className="text-sm font-medium text-gray-700">Manufacturer</p>
                        <p className="text-gray-900">{selectedSensor.sensor.sensor_type.manufacturer}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                      <Cpu className="w-4 h-4 text-gray-400" />
                      <div>
                        <p className="text-sm font-medium text-gray-700">Pin Configuration</p>
                        <p className="text-gray-900 font-mono">{selectedSensor.sensor.pin}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Latest Readings */}
                <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Activity className="w-5 h-5 text-emerald-600" />
                    Latest Readings
                  </h3>
                  
                  {selectedSensor.sensordatavalues.length > 0 ? (
                    <div className="space-y-2">
                      {selectedSensor.sensordatavalues.map((data) => (
                        <div 
                          key={data.id}
                          className="flex items-center justify-between p-3 bg-emerald-50 rounded-xl border border-emerald-100"
                        >
                          <div className="flex items-center gap-3">
                            <ChevronRight className="w-4 h-4 text-emerald-600" />
                            <span className="font-medium text-gray-700">
                              {data.value_type}
                            </span>
                          </div>
                          <span className="font-bold text-emerald-700 text-lg">
                            {data.value}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-6 text-gray-500">
                      <Activity className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                      <p className="text-sm">No recent data available</p>
                    </div>
                  )}
                </div>

                {/* Timestamp */}
                <div className="flex items-center gap-2 p-4 bg-blue-50 rounded-xl border border-blue-100">
                  <Clock className="w-4 h-4 text-blue-600" />
                  <div>
                    <p className="text-sm font-medium text-blue-700">Last Updated</p>
                    <p className="text-blue-800 font-medium">
                      {new Date(selectedSensor.timestamp).toLocaleString('en-US', {
                        weekday: 'short',
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT MAP PANEL */}
        <div className="flex-1 relative">
          <Map
            mapId={import.meta.env.VITE_GOOGLE_MAP_ID}
            defaultZoom={3}
            defaultCenter={{ lat: -1.310779, lng: 36.816999 }}
            className="w-full h-full"
          >
            <Markers liveData={liveData} onSelect={setSelectedSensor} />
          </Map>
          
          {/* Map Controls Overlay */}
          <div className="absolute top-4 right-4 bg-white rounded-xl shadow-lg border border-gray-200 p-3">
            <p className="text-xs font-medium text-gray-600 mb-1">Active Sensors</p>
            <p className="text-2xl font-bold text-blue-600">{liveData.length}</p>
          </div>
        </div>
      </div>
    </APIProvider>
  );
}

// ----------------- Marker + Clustering -----------------
function Markers({
  liveData,
  onSelect,
}: {
  liveData: LiveData[];
  onSelect: (sensor: LiveData) => void;
}) {
  const map = useMap();
  const [markers, setMarkers] = useState<{ [key: string]: Marker }>({});
  const clusterer = useRef<MarkerClusterer | null>(null);

  useEffect(() => {
    if (!map) return;
    if (!clusterer.current) {
      clusterer.current = new MarkerClusterer({ 
        map,
        renderer: {
          render: ({ count, position }) => {
            const color = count > 10 ? '#dc2626' : count > 5 ? '#ea580c' : '#059669';
            return new google.maps.Marker({
              position,
              icon: {
                path: google.maps.SymbolPath.CIRCLE,
                fillColor: color,
                fillOpacity: 0.9,
                strokeWeight: 3,
                strokeColor: '#ffffff',
                scale: Math.min(count * 3 + 15, 40),
              },
              label: {
                text: count.toString(),
                color: '#ffffff',
                fontWeight: 'bold',
                fontSize: '14px'
              },
              zIndex: 1000,
            });
          },
        }
      });
    }
  }, [map]);

  useEffect(() => {
    clusterer.current?.clearMarkers();
    clusterer.current?.addMarkers(Object.values(markers));
  }, [markers]);

  const setMarkerRef = (marker: Marker | null, key: string) => {
    if (marker && markers[key]) return;
    if (!marker && !markers[key]) return;

    setMarkers((prev) => {
      if (marker) {
        return { ...prev, [key]: marker };
      } else {
        const newMarkers = { ...prev };
        delete newMarkers[key];
        return newMarkers;
      }
    });
  };

  return (
    <>
      {liveData.filter(sensor => {
        const lat = parseFloat(sensor.location.latitude);
        const lng = parseFloat(sensor.location.longitude);
        return !isNaN(lat) && !isNaN(lng);
      }).map((sensor) => {
        const hasData = sensor.sensordatavalues.length > 0;
        
        return (
          <AdvancedMarker
            key={sensor.id}
            position={{
              lat: parseFloat(sensor.location.latitude),
              lng: parseFloat(sensor.location.longitude),
            }}
            ref={(marker) => setMarkerRef(marker, sensor.id.toString())}
            onClick={() => onSelect(sensor)}
          >
            <div className="flex flex-col items-center cursor-pointer transform transition-all duration-200 hover:scale-110">
              {/* Main sensor icon */}
              <div className={`
                relative p-3 rounded-2xl shadow-lg border-2 bg-white
                ${hasData 
                  ? 'border-emerald-400 text-emerald-600' 
                  : 'border-gray-300 text-gray-400'
                }
                hover:shadow-xl transition-all duration-200
              `}>
                <Radio className="w-6 h-6" />
                
                {/* Status indicator */}
                <div className={`
                  absolute -top-1 -right-1 w-4 h-4 rounded-full border-2 border-white
                  ${hasData ? 'bg-emerald-500' : 'bg-gray-400'}
                  animate-pulse
                `} />
              </div>
              
              {/* Sensor ID label */}
              <div className={`
                mt-2 px-2 py-1 rounded-lg text-xs font-semibold shadow-md
                ${hasData 
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' 
                  : 'bg-gray-100 text-gray-600 border border-gray-200'
                }
              `}>
                #{sensor.sensor.id}
              </div>
            </div>
          </AdvancedMarker>
        );
      })}
    </>
  );
}