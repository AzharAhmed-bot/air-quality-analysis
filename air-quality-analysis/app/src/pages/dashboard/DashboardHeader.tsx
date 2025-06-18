import CornerElement from "../../components/CornerElement"
import type { LocationProps } from "../../types"
import Country from "./Country"
import LocationPopUp from "./LocationPopUp"

interface DashboardHeaderProps {
  locations: LocationProps[]
  selectedCountry: string
  setSelectedCountry: (country: string) => void
  filteredLocations: LocationProps[]
  total: number
}
function DashboardHeader({locations, selectedCountry, setSelectedCountry, filteredLocations,total}: DashboardHeaderProps) {
  return (
    <div className="relative backdrop-blur-sm border border-border p-6 rounded-lg">
      <CornerElement />

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        {/* Left */}
        <div className="flex items-center gap-6">
          <div className="relative">
              <div className="w-24 h-24 rounded-lg bg-gradient-to-br from-primary/30 to-secondary/30 flex items-center justify-center">
                <span className="text-3xl font-bold text-primary">🌍</span>
              </div>
            <div className="absolute bottom-0 right-0 w-4 h-4 rounded-full bg-green-500 border-2 border-background"></div>
          </div>

          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              {selectedCountry || "Select a Country"}
            </h1>
            <p className="text-sm text-muted-foreground font-mono">
              {total} Sensor Location(s) Found
            </p>

            <div className="flex items-center bg-cyber-terminal-bg backdrop-blur-sm border border-border rounded px-3 py-1 mt-2 w-fit">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse mr-2"></div>
              <p className="text-xs font-mono text-primary">SENSORS ACTIVE</p>
            </div>
          </div>
        </div>

        {/* Right */}
        <div className="flex flex-col md:items-end gap-2">
          <Country
            locations={locations}
            selectedCountry={selectedCountry}
            setSelectedCountry={setSelectedCountry}
          />
          {/* <Button variant='outline' className="border-primary/50 text-primary dark:hover:text-white hover:text-black  hover:bg-primary/10">
            View All Locations
          </Button> */}
            {selectedCountry && (
                <LocationPopUp
                selectedCountry={selectedCountry}
                filteredLocations={filteredLocations}
                />
            )}

        </div>
      </div>
    </div>
  )
}

export default DashboardHeader