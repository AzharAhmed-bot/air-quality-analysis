import { configureStore } from '@reduxjs/toolkit';
import locationSlice from './locationSlicer';
import liveDataSlice from './liveDataSlicer';


export const store = configureStore({
  reducer: {
    location: locationSlice,
    liveData: liveDataSlice,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;