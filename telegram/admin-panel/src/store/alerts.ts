import { create } from "zustand";

export interface ToastItem {
  id: number;
  type: "NEW_ORDER" | "PAYMENT_SUBMITTED" | "INFO";
  title: string;
  description?: string;
  link?: string;
}

interface AlertsState {
  toasts: ToastItem[];
  push: (t: Omit<ToastItem, "id">) => void;
  dismiss: (id: number) => void;
}

let nextId = 1;

export const useAlerts = create<AlertsState>((set) => ({
  toasts: [],
  push: (t) =>
    set((state) => ({
      toasts: [{ id: nextId++, ...t }, ...state.toasts].slice(0, 5),
    })),
  dismiss: (id) =>
    set((state) => ({ toasts: state.toasts.filter((x) => x.id !== id) })),
}));
