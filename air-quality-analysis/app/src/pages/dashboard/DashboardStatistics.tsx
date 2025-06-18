import CornerElement from "../../components/CornerElement"

interface StatsProps {
  stats: {
    total: number
    indoor: number
    outdoor: number
    withTraffic: number
    withIndustry: number
    withOven: number
  }
}

function DashboardStatistics({ stats }: StatsProps) {
  return (
    <div className="space-y-8 mt-8">
      <div className="relative backdrop-blur-sm border border-border p-6 rounded-lg">
        <CornerElement />

        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold tracking-tight">
            <span className="text-primary">Your</span>{" "}
            <span className="text-foreground">Statistics</span>
          </h2>
          <div className="font-mono text-xs text-muted-foreground">
            TOTAL: <span className="text-foreground font-semibold">{stats.total}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4 text-center text-xs font-mono text-muted-foreground">
          <div className="bg-muted p-4 rounded-lg">
            <p className="text-lg font-bold text-foreground">{stats.indoor}</p>
            <p>Indoor</p>
          </div>
          <div className="bg-muted p-4 rounded-lg">
            <p className="text-lg font-bold text-foreground">{stats.outdoor}</p>
            <p>Outdoor</p>
          </div>
          <div className="bg-muted p-4 rounded-lg">
            <p className="text-lg font-bold text-foreground">{stats.withTraffic}</p>
            <p>Traffic Area</p>
          </div>
          <div className="bg-muted p-4 rounded-lg">
            <p className="text-lg font-bold text-foreground">{stats.withIndustry}</p>
            <p>Industry Area</p>
          </div>
          <div className="bg-muted p-4 rounded-lg">
            <p className="text-lg font-bold text-foreground">{stats.withOven}</p>
            <p>Oven Area</p>
          </div>
          <div className="bg-muted p-4 rounded-lg">
            <p className="text-lg font-bold text-foreground">{stats.total}</p>
            <p>Total</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardStatistics
