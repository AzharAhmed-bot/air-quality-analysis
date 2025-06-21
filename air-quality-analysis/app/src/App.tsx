
import { useEffect } from "react"
import { fetchLocations } from "../redux/locationSlicer"
import { fetchLiveData } from "../redux/liveDataSlicer"
import { useDispatch, useSelector } from "react-redux"
import type { AppDispatch, RootState } from "../redux/store"
import Dashboard from "./pages/dashboard/Dashboard"

// ...existing code...

function App() {
  const dispatch = useDispatch<AppDispatch>()
  const locations = useSelector((state: RootState) => state.location.locations)
  const liveData = useSelector((state: RootState) => state.liveData.liveData)


  useEffect(() => {
    dispatch(fetchLocations())
    dispatch(fetchLiveData())
  }, [dispatch])




  return (
    <>
      <Dashboard locations={locations} liveData={liveData}/>
    </>
  )
}

export default App