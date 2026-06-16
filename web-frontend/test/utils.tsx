import type React from "react";
import { configureStore } from "@reduxjs/toolkit";
import { type RenderOptions, render } from "@testing-library/react";
import { Provider } from "react-redux";
import { BrowserRouter } from "react-router-dom";
import { api } from "@/store/api";
import authReducer from "@/store/authSlice";
import transactionReducer from "@/store/transactionSlice";
import uiReducer from "@/store/uiSlice";
import walletReducer from "@/store/walletSlice";
import type { RootState } from "@/store";

const createTestStore = (preloadedState?: Partial<RootState>) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      wallet: walletReducer,
      transactions: transactionReducer,
      ui: uiReducer,
      [api.reducerPath]: api.reducer,
    },
    // configureStore's preloadedState expects the full RootState shape. Test
    // callers intentionally pass a partial slice, so cast to satisfy the
    // overload; RTK merges partial preloaded state at runtime.
    preloadedState: preloadedState as RootState | undefined,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: false,
      }).concat(api.middleware),
  });
};

interface ExtendedRenderOptions extends Omit<RenderOptions, "wrapper"> {
  preloadedState?: Partial<RootState>;
  store?: ReturnType<typeof createTestStore>;
}

export const renderWithProviders = (
  ui: React.ReactElement,
  {
    preloadedState = {},
    store = createTestStore(preloadedState),
    ...renderOptions
  }: ExtendedRenderOptions = {},
) => {
  const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    return (
      <Provider store={store}>
        <BrowserRouter>{children}</BrowserRouter>
      </Provider>
    );
  };

  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) };
};

// Mock user aligned with actual User type from @/types
export const mockUser = {
  id: "1",
  email: "test@example.com",
  firstName: "Test",
  lastName: "User",
  fullName: "Test User",
  role: "customer" as const,
  permissions: [],
  isEmailVerified: true,
  isPhoneVerified: false,
  kycStatus: "completed" as const,
  mfaEnabled: false,
  status: "active" as const,
  createdAt: "2023-01-01T00:00:00Z",
  updatedAt: "2023-01-01T00:00:00Z",
};

export const mockWallet = {
  id: "1",
  userId: "1",
  balance: 1000,
  currency: "USD",
  type: "checking" as const,
  isActive: true,
  createdAt: "2023-01-01T00:00:00Z",
  updatedAt: "2023-01-01T00:00:00Z",
};

export const mockTransaction = {
  id: "1",
  walletId: "1",
  type: "deposit" as const,
  amount: 100,
  currency: "USD",
  description: "Test transaction",
  category: "income" as const,
  status: "completed" as const,
  createdAt: "2023-01-01T00:00:00Z",
  updatedAt: "2023-01-01T00:00:00Z",
};

export * from "@testing-library/react";
export { renderWithProviders as render };
