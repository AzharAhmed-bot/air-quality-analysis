import { useState } from 'react'
import type { LocationProps } from '../../types'
import DashboardHeader from './DashboardHeader'

function Dashboard({ locations }: { locations: LocationProps[] }) {
  const [selectedCountry, setSelectedCountry] = useState<string>('')

  return (
    <div className="p-6 space-y-6">
      {/* Dashboard Header */}
      <DashboardHeader
        locations={locations}
        selectedCountry={selectedCountry}
        setSelectedCountry={setSelectedCountry}
      />
    </div>
  )
}

export default Dashboard
