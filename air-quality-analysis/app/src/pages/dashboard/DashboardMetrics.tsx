import { Tabs,TabsList, TabsTrigger, TabsContent } from '../../components/ui/tabs'
import CornerElement from '../../components/CornerElement'

function DashboardMetrics() {
  return (
    <>
        {/* Metrics Section */}
      <div className="relative backdrop-blur-sm border border-border rounded-lg p-6">
        <CornerElement/>
        <div className="flex items-center gap-2 mb-4">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
            <h3 className="text-lg font-bold">
            Metrics
          </h3>
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
        </Tabs>
      </div>
    </>
  )
}

export default DashboardMetrics