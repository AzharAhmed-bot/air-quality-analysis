
import DashboardStatistics from "./DashboardStatistics"
import SearchLocation from "./SearchLocation"
import type { LocationProps,SensorData } from "../../types"
import { useEffect, useState } from "react"
import DashboardHeader from "./DashboardHeader"


interface LocationComponentProps {
  locations: LocationProps[]
  liveData?: SensorData[]

}

function Dashboard({
  locations,
  liveData
}: LocationComponentProps) {
  const [selectedCountry, setSelectedCountry] = useState<string>('')
  const [filteredLocations, setFilteredLocations] = useState<LocationProps[]>([])



  useEffect(() => {
    if (selectedCountry) {
      const filtered: LocationProps[] = locations.filter(
        (location: LocationProps) => location.country === selectedCountry
      )
      setFilteredLocations(filtered)
    }
  }, [locations, selectedCountry])

  // === Aggregate Stats ===
  const total = filteredLocations.length
  const indoor = filteredLocations.filter((loc) => loc.indoor).length
  const outdoor = total - indoor
  const withTraffic = filteredLocations.filter((loc) => loc.traffic_in_area).length
  const withIndustry = filteredLocations.filter((loc) => loc.industry_in_area).length
  const withOven = filteredLocations.filter((loc) => loc.oven_in_area).length

  return (
    <section className="relative z-10 pt-12 pb-32 flex-grow container mx-auto px-4">
    <DashboardHeader locations={locations} selectedCountry={selectedCountry} setSelectedCountry={setSelectedCountry} filteredLocations={filteredLocations} total={total} />
    <DashboardStatistics
      stats={{
        total,
        indoor,
        outdoor,
        withTraffic,
        withIndustry,
        withOven,
      }}
    />
    {
      selectedCountry && (
        <>
        <SearchLocation
          filteredLocations={filteredLocations.map((loc) => ({
            ...loc,
            id: String(loc.id),
          }))}
        />
        
        </>
    )}
    


    </section>
  )
}

export default Dashboard
