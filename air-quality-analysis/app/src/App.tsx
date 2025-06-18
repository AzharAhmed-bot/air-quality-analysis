
import { useEffect } from "react"
import { fetchLocations } from "../redux/locationSlicer"
import { useDispatch, useSelector } from "react-redux"
import type { AppDispatch, RootState } from "../redux/store"
import Dashboard from "./pages/dashboard/Dashboard"

// ...existing code...

function App() {
  const dispatch = useDispatch<AppDispatch>()
  const locations = useSelector((state: RootState) => state.location.locations)


  useEffect(() => {
    dispatch(fetchLocations())
  }, [dispatch])




  return (
    <>
      <Dashboard locations={locations}/>
    </>
  )
}

export default App