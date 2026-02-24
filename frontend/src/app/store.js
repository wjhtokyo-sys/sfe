import { configureStore } from '@reduxjs/toolkit';
import sfeReducer from '../features/sfeSlice';

export const store = configureStore({
  reducer: { sfe: sfeReducer },
});
