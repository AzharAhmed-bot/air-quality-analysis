import { createAsyncThunk,createSlice } from '@reduxjs/toolkit';
import { getLiveData } from '../src/api/api';

export const fetchLiveData = createAsyncThunk(
    '/data/fetchLiveData',
    async () =>{
        const liveData = await getLiveData();
        return liveData;
    }
)

const initialState = {
    isLoading: false,
    liveData: [],
    error: null as string | null
}

const liveDataSlice = createSlice({
    name: 'liveData',
    initialState:initialState,
    reducers:{},
    extraReducers: (builder)=>{
        builder.addCase(fetchLiveData.pending,(state)=>{
            state.isLoading = true
        });
        builder.addCase(fetchLiveData.fulfilled,(state,action)=>{
            state.isLoading = false
            state.liveData = action.payload
        });
        builder.addCase(fetchLiveData.rejected,(state,action)=>{
            state.isLoading = false
            state.error = action.error.message ?? null
        })
    }
})

export default liveDataSlice.reducer