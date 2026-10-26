"use client";

import { useSyncExternalStore } from "react";

const emptySubscribe = () => () => {};

/**
 * True after the first client render. Use to gate UI that depends on
 * persisted client state (e.g. zustand localStorage rehydration) so
 * server-rendered markup matches the first client render.
 */
export function useMounted(): boolean {
  return useSyncExternalStore(
    emptySubscribe,
    () => true, // client snapshot
    () => false, // server snapshot
  );
}
