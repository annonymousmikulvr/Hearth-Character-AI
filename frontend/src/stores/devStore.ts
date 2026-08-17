import { create } from "zustand";

interface DevState {
  devMode: boolean;
  setDevMode: (v: boolean) => void;
}

function load(): boolean {
  try {
    return localStorage.getItem("hearth-dev-mode") === "1";
  } catch {
    return false;
  }
}

export const useDevStore = create<DevState>((set) => ({
  devMode: load(),
  setDevMode: (devMode) => {
    try {
      localStorage.setItem("hearth-dev-mode", devMode ? "1" : "0");
    } catch {
      /* ignore */
    }
    set({ devMode });
  },
}));
