import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UiState {
  /** Desktop sidebar collapsed to the icon rail. Persisted across reloads. */
  collapsed: boolean;
  toggleSidebar: () => void;
}

/**
 * Layout preferences. Deliberately separate from `auth-storage` so logging
 * out does not reset how the app looks.
 */
export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      collapsed: false,
      toggleSidebar: () => set((state) => ({ collapsed: !state.collapsed })),
    }),
    { name: "ui-preferences", version: 1 },
  ),
);
