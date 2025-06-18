import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "../../components/ui/alert-dialog";
import type { LocationProps } from "../../types";
import { Button } from "../../components/ui/button";

interface LocationPopUpProps {
  selectedCountry: string;
  filteredLocations: LocationProps[];
}

function LocationPopUp({ selectedCountry, filteredLocations }: LocationPopUpProps) {
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="outline" className="border-primary/50 text-primary dark:hover:text-white hover:text-black  hover:bg-primary/10">View All Locations</Button>
      </AlertDialogTrigger>
      <AlertDialogContent className="bg-white text-foreground p-6 rounded-xl shadow-2xl w-full max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="text-2xl font-semibold mb-2">
            Locations in <span className="text-primary">{selectedCountry}</span>
          </AlertDialogTitle>
        </AlertDialogHeader>

        <div className="max-h-[250px] overflow-y-auto mt-2 space-y-2 pr-2 scrollbar-thin scrollbar-thumb-primary/40 scrollbar-track-muted/10">
          {filteredLocations.map((location) => (
            <div
              key={location.id}
              className="bg-muted/50 px-4 py-2 rounded-md flex items-center gap-3 hover:bg-muted transition"
            >
              {/* <div className="w-2 h-2 rounded-full bg-primary"></div> */}
              <span className="text-sm font-medium">{location.location}</span>
            </div>
          ))}
        </div>

        <div className="flex justify-end mt-4">
          <AlertDialogCancel className="mt-0">Close</AlertDialogCancel>
        </div>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export default LocationPopUp;
