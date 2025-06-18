import  {Select,SelectContent,SelectTrigger,SelectValue,SelectItem} from '../../components/ui/select'
import { useEffect,useState } from 'react'
import type { LocationProps } from '../../types'


interface CountryProps {
  locations: LocationProps[]
  selectedCountry: string
  setSelectedCountry: (country: string) => void
}

function Country({locations,selectedCountry,setSelectedCountry}: CountryProps) {
    const [countries,setCountries]=useState<string[]>([])

 
  useEffect(() => {
    if(locations.length !==0){
        const allCountries = Array.from(
          new Set(
            locations
              .map((location: LocationProps) => location.country)
              .filter((country) => !!country && country.trim() !== "")
          )
        ).sort();
        setCountries(allCountries)
    }
  }, [locations])
  return (
    <Select value={selectedCountry} onValueChange={setSelectedCountry}>
      <SelectTrigger>
        <SelectValue placeholder='country'/>
      </SelectTrigger>
      <SelectContent>
        {countries.map((country) => (
          <SelectItem  key={country} value={country}>
            {country}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

export default Country