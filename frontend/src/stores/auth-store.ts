import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { UserResponse } from "@/types/api";

interface AuthState {
  token: string | null;
  user: UserResponse | null;
  /** True once the persisted state has been read on the client. */
  hydrated: boolean;
  setAuth: (token: string, user: UserResponse | null) => void;
  setToken: (token: string) => void;
  setUser: (user: UserResponse) => void;
  clearAuth: () => void;
  setHydrated: () => void;
}

/**
 * Client-side auth state. Access token persisted to localStorage;
 * the refresh token lives in an HttpOnly cookie managed by the backend.
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      hydrated: false,
      setAuth: (token, user) => set({ token, user }),
      setToken: (token) => set({ token }),
      setUser: (user) => set({ user }),
      clearAuth: () => set({ token: null, user: null }),
      setHydrated: () => set({ hydrated: true }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({ token: state.token, user: state.user }),
      onRehydrateStorage: () => (state) => {
        state?.setHydrated();
      },
    },
  ),
);
