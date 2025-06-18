import { createAsyncThunk,createSlice } from "@reduxjs/toolkit";
import { getLocations } from "../src/api/locations";
import type {LocationProps} from "../src/types";



export const fetchLocations = createAsyncThunk(
    'data/fetchLocations',
    async ()=>{
        const locations = await getLocations();
        return locations;
    }
)

const initialStates ={
    isLoading: false,
    locations: [] as LocationProps[],
    error: null as string | null
}

const locationSlice = createSlice({
    name:'location',
    initialState:initialStates,
    reducers: {},
    extraReducers: (builder)=>{
        builder.addCase(fetchLocations.pending,(state)=>{
            state.isLoading = true
        });
        builder.addCase(fetchLocations.fulfilled,(state,action)=>{
            state.isLoading = false
            state.locations = action.payload
        });
        builder.addCase(fetchLocations.rejected,(state,action)=>{
            state.isLoading = false
            state.error = action.error.message ?? null
        });
    }
})

export default locationSlice.reducer