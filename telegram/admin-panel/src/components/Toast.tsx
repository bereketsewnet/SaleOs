import { useEffect } from "react";
import { Link } from "react-router-dom";
import {
  HiOutlineBell,
  HiOutlineCheckCircle,
  HiOutlineInformationCircle,
  HiOutlineXMark,
  HiArrowRight,
} from "react-icons/hi2";
import { useAlerts, type ToastItem } from "../store/alerts";

export function ToastStack() {
  const toasts = useAlerts((s) => s.toasts);
  return (
    <div className="fixed top-20 right-4 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
      {toasts.map((t) => (
        <Toast key={t.id} toast={t} />
      ))}
    </div>
  );
}

const TONE: Record<ToastItem["type"], { ring: string; bg: string; Icon: React.ComponentType<{ className?: string }> }> = {
  NEW_ORDER: {
    ring: "ring-emerald-200",
    bg: "bg-emerald-50 text-emerald-700",
    Icon: HiOutlineBell,
  },
  PAYMENT_SUBMITTED: {
    ring: "ring-amber-200",
    bg: "bg-amber-50 text-amber-700",
    Icon: HiOutlineCheckCircle,
  },
  INFO: {
    ring: "ring-slate-200",
    bg: "bg-slate-100 text-slate-600",
    Icon: HiOutlineInformationCircle,
  },
};

function Toast({ toast }: { toast: ToastItem }) {
  const dismiss = useAlerts((s) => s.dismiss);
  useEffect(() => {
    const timer = setTimeout(() => dismiss(toast.id), 8000);
    return () => clearTimeout(timer);
  }, [toast.id, dismiss]);

  const tone = TONE[toast.type] ?? TONE.INFO;
  const Icon = tone.Icon;
  return (
    <div
      className={`pointer-events-auto rounded-2xl bg-white p-3.5 shadow-lg ring-1 ${tone.ring} animate-slide-up`}
    >
      <div className="flex items-start gap-3">
        <div className={`w-9 h-9 rounded-xl grid place-items-center shrink-0 ${tone.bg}`}>
          <Icon className="w-5 h-5" />
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
              className="mt-1.5 inline-flex items-center gap-1 text-xs text-brand-700 font-semibold hover:text-brand-800"
            >
              View order <HiArrowRight className="w-3 h-3" />
            </Link>
          )}
        </div>
        <button
          onClick={() => dismiss(toast.id)}
          aria-label="Dismiss"
          className="text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg p-1 transition"
        >
          <HiOutlineXMark className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
