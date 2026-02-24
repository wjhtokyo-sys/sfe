import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import { api } from '../api/client';

export const loadDashboard = createAsyncThunk('sfe/load', async () => {
  const [customers, items, orders, lots, allocations, bills] = await Promise.all([
    api.get('/customers'), api.get('/items'), api.get('/orders'), api.get('/lots'), api.get('/allocations'), api.get('/bills')
  ]);
  return {
    customers: customers.data,
    items: items.data,
    orders: orders.data,
    lots: lots.data,
    allocations: allocations.data,
    bills: bills.data,
  };
});

const slice = createSlice({
  name: 'sfe',
  initialState: { customers: [], items: [], orders: [], lots: [], allocations: [], bills: [], loading: false },
  reducers: {},
  extraReducers: (builder) => {
    builder.addCase(loadDashboard.pending, (state) => { state.loading = true; });
    builder.addCase(loadDashboard.fulfilled, (state, action) => { Object.assign(state, action.payload); state.loading = false; });
  },
});

export default slice.reducer;
