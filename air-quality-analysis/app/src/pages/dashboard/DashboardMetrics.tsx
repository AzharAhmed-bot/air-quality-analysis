import { Tabs, TabsList, TabsTrigger, TabsContent } from '../../components/ui/tabs';
import CornerElement from '../../components/CornerElement';
import type { SensorData } from "../../types";
import { Card, CardContent } from "../../components/ui/card"
import {Table, TableBody, TableCell, TableHead, TableHeader, TableRow} from "../../components/ui/table"
import { Alert, AlertDescription, AlertTitle } from "../../components/ui/alert"



interface DashboardMetricsProps {
  liveData?: SensorData[];
  locationId: number | null;
}

function DashboardMetrics({ liveData, locationId }: DashboardMetricsProps) {
  // Correct filtering based on the actual structure
  const filteredData = liveData?.filter(
    (data) => data.location.id === locationId
  ) || [];

  return (
    <div className="relative backdrop-blur-sm border border-border rounded-lg p-6">
      <CornerElement />
      <div className="flex items-center gap-2 mb-4">
        <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
        <h3 className="text-lg font-bold">Metrics</h3>
      </div>

      <Tabs defaultValue="statistics" className="w-full">
        <TabsList className="mb-6 w-full grid grid-cols-3 bg-cyber-terminal-bg border">
          <TabsTrigger value="statistics" className="w-full text-center">
            Sensor Readings
          </TabsTrigger>
          <TabsTrigger value="locations" className="w-full text-center">
            Predictions
          </TabsTrigger>
          <TabsTrigger value="sensors" className="w-full text-center">
            Recommendations
          </TabsTrigger>
        </TabsList>

        <TabsContent value="statistics">
          {filteredData && filteredData.length > 0 ? (
            <ul className="text-sm space-y-4">
              {filteredData.map((reading) => (
                <li key={reading.id} className="p-2 rounded bg-muted">
                  <strong>Timestamp:</strong> {reading.timestamp}
                  <ul className="ml-4 mt-1 space-y-1">
                    {reading.sensordatavalues.map((val) => (
                      <li key={val.id}>
                        <strong>{val.value_type}:</strong> {val.value}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted-foreground text-sm">
              No sensor data available for this location.
            </p>
          )}
        </TabsContent>

        <TabsContent value="locations">
          <p className="text-sm text-muted-foreground">Prediction data coming soon...</p>
        </TabsContent>

        <TabsContent value="sensors">
          <p className="text-sm text-muted-foreground">Recommendations will appear here.</p>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default DashboardMetrics;
