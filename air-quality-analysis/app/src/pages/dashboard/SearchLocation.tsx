import { useState } from "react";
import { Input } from "../../components/ui/input";
import { XIcon } from "lucide-react";
import { Button } from "../../components/ui/button";
import DashboardMetrics from "./DashboardMetrics";

interface Location {
  id: string;
  location: string;
}

interface SearchLocationProps {
  filteredLocations: Location[];
}

function SearchLocation({ filteredLocations }: SearchLocationProps) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<Location[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);

    const filtered = filteredLocations
      .filter(
        (loc) =>
          loc.location.toLowerCase().includes(value.toLowerCase()) &&
          loc.location !== selectedLocation?.location
      )
      .slice(0, 5);
    setSuggestions(filtered);
  };

  const handleSelect = (loc: Location) => {
    setSelectedLocation(loc);
    setQuery("");
    setSuggestions([]);
    console.log("Selected Location ID:", loc.id); // 👈 Print the ID
  };

  const handleRemove = () => {
    setSelectedLocation(null);
  };

  return (
    <div className="flex flex-col gap-4">
    <div className="relative w-full  mt-4">
      <div className="flex w-full items-center gap-2">
        {/* Search Input */}
        <Input
          placeholder="Search Location"
          value={query}
          onChange={handleChange}
          className="rounded-lg flex-1 max-w-md"
          disabled={selectedLocation !== null}
        />

        {/* Selected Location Tag */}
        {selectedLocation && (
          <div className="flex items-center bg-muted px-3 py-1 rounded-full text-sm max-w-full whitespace-nowrap overflow-hidden">
            <span className="truncate pr-2 border-1 rounded-lg p-1 cursor-pointer bg-gray-200 border-primary/50 text-primary dark:hover:text-white hover:text-black  hover:bg-primary/10">
              {selectedLocation.location}
            </span>
            <Button
              variant="ghost"
              onClick={handleRemove}
              size="icon"
              className="w-5 h-5 p-0 hover:text-destructive"
            >
              <XIcon className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Suggestions */}
      {query.length > 0 && suggestions.length > 0 && (
        <div className="absolute z-10 mt-1 bg-white border border-border rounded-md shadow-lg w-full max-h-60 overflow-y-auto">
          {suggestions.map((loc) => (
            <div
              key={loc.id}
              onClick={() => handleSelect(loc)}
              className="px-4 py-2 cursor-pointer hover:bg-muted text-sm"
            >
              {loc.location}
            </div>
          ))}
        </div>
      )}
    </div>
    <div>
      <DashboardMetrics/>
    </div>
    </div>
  );
}

export default SearchLocation;
