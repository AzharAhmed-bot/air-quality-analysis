export interface LocationProps {
    id: number;
    location: string;
    country: string;
    indoor: boolean;
    latitude: string;
    longitude: string;
    traffic_in_area: number;
    oven_in_area: number;
    industry_in_area: number;
}
export interface SensorData {
  id: number;
  sampling_rate: string | null;
  timestamp: string;
  sensordatavalues: SensorValue[];
  location: Location;
  sensor: Sensor;
}

export interface SensorValue {
  id: number;
  value: string;
  value_type: string;
}

export interface Location {
  id: number;
  latitude: string;
  longitude: string;
}

export interface Sensor {
  id: number;
  pin: string;
  sensor_type: SensorType;
}

export interface SensorType {
  id: number;
  name: string;
  manufacturer: string;
}
