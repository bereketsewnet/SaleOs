import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useAlerts, type ToastItem } from "../store/alerts";

export function ToastStack() {
  const toasts = useAlerts((s) => s.toasts);
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => (
        <Toast key={t.id} toast={t} />
      ))}
    </div>
  );
}

function Toast({ toast }: { toast: ToastItem }) {
  const dismiss = useAlerts((s) => s.dismiss);
  useEffect(() => {
    const timer = setTimeout(() => dismiss(toast.id), 8000);
    return () => clearTimeout(timer);
  }, [toast.id, dismiss]);

  const isOrder = toast.type === "NEW_ORDER";
  return (
    <div
      className={`rounded-2xl shadow-lg border p-3 bg-white animate-[fadeIn_.2s_ease-out] ${
        isOrder ? "border-emerald-300" : "border-slate-200"
      }`}
    >
      <div className="flex items-start gap-3">
        <div className={`text-xl ${isOrder ? "" : "opacity-70"}`}>
          {isOrder ? "🛎️" : "ℹ️"}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-slate-900 text-sm">{toast.title}</p>
          {toast.description && (
            <p className="text-xs text-slate-600 mt-0.5 line-clamp-2">{toast.description}</p>
          )}
          {toast.link && (
            <Link
              to={toast.link}
              onClick={() => dismiss(toast.id)}
              className="inline-block mt-1 text-xs text-brand-700 font-medium"
            >
              View →
            </Link>
          )}
        </div>
        <button
          onClick={() => dismiss(toast.id)}
          className="text-slate-400 hover:text-slate-700 text-lg leading-none"
        >
          ×
        </button>
      </div>
    </div>
  );
}
