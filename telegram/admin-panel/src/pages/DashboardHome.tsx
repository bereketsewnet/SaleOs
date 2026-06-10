import { Link } from "react-router-dom";
import {
  HiOutlineCube,
  HiOutlineDocumentText,
  HiOutlineBanknotes,
  HiOutlineClipboardDocumentCheck,
  HiOutlineCog6Tooth,
  HiOutlineSparkles,
  HiArrowRight,
  HiOutlineChatBubbleLeftRight,
} from "react-icons/hi2";
import { useAuthStore } from "../store/auth";

export default function DashboardHome() {
  const user = useAuthStore((s) => s.user);
  const greeting = useGreeting();

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-600 via-brand-500 to-sky-400 text-white p-6 sm:p-8 shadow-lg">
        <div className="absolute -top-12 -right-12 w-56 h-56 bg-white/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-12 -left-12 w-48 h-48 bg-white/10 rounded-full blur-3xl" />
        <div className="relative">
          <p className="text-xs uppercase tracking-widest opacity-80 mb-1">{greeting}</p>
          <h1 className="text-2xl sm:text-3xl font-bold leading-tight">
            Welcome back, {user?.first_name} 👋
          </h1>
          <p className="mt-1.5 text-sm sm:text-base opacity-90 max-w-xl">
            Here's a snapshot of your Telegram-first commerce business.
          </p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat title="Orders today" value="0" Icon={HiOutlineDocumentText} tone="brand" />
        <Stat title="Revenue today" value="ETB 0" Icon={HiOutlineBanknotes} tone="emerald" />
        <Stat title="Products live" value="0" Icon={HiOutlineCube} tone="amber" />
        <Stat title="Pending reviews" value="0" Icon={HiOutlineClipboardDocumentCheck} tone="rose" />
      </div>

      {/* Getting started + Quick actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <section className="lg:col-span-2 card card-pad">
          <div className="flex items-center gap-2 mb-4">
            <HiOutlineSparkles className="w-5 h-5 text-brand-600" />
            <h2 className="section-title">Getting started</h2>
          </div>
          <ol className="space-y-3">
            <Step n={1} title="Connect your Telegram bot" desc="Settings → Telegram bot, paste the bot token." />
            <Step n={2} title="Add payment accounts" desc="Settings → Payment accounts. Customers pay you direct." />
            <Step n={3} title="Add your first product" desc="Products → New product. Or post #product in your channel." />
            <Step n={4} title="Promote your channel" desc="Share the bot link or Mini App URL to start receiving orders." />
          </ol>
        </section>

        <section className="card card-pad">
          <div className="flex items-center gap-2 mb-4">
            <HiOutlineChatBubbleLeftRight className="w-5 h-5 text-brand-600" />
            <h2 className="section-title">Jump in</h2>
          </div>
          <div className="space-y-2">
            <QuickAction to="/products" label="Manage products" Icon={HiOutlineCube} />
            <QuickAction to="/orders" label="View orders" Icon={HiOutlineDocumentText} />
            <QuickAction to="/settings" label="Open settings" Icon={HiOutlineCog6Tooth} />
          </div>
        </section>
      </div>
    </div>
  );
}

const TONES: Record<string, { wrap: string; icon: string }> = {
  brand: { wrap: "bg-brand-50", icon: "text-brand-700" },
  emerald: { wrap: "bg-emerald-50", icon: "text-emerald-700" },
  amber: { wrap: "bg-amber-50", icon: "text-amber-700" },
  rose: { wrap: "bg-rose-50", icon: "text-rose-700" },
};

function Stat({
  title,
  value,
  Icon,
  tone,
}: {
  title: string;
  value: string;
  Icon: React.ComponentType<{ className?: string }>;
  tone: keyof typeof TONES;
}) {
  const t = TONES[tone];
  return (
    <div className="card card-pad relative overflow-hidden">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-slate-500 font-semibold">{title}</p>
          <p className="text-2xl sm:text-3xl font-bold text-slate-900 mt-1.5">{value}</p>
        </div>
        <div className={`w-10 h-10 rounded-xl grid place-items-center ${t.wrap}`}>
          <Icon className={`w-5 h-5 ${t.icon}`} />
        </div>
      </div>
    </div>
  );
}

function Step({ n, title, desc }: { n: number; title: string; desc: string }) {
  return (
    <li className="flex gap-3.5">
      <div className="w-7 h-7 rounded-full bg-brand-100 text-brand-700 font-bold text-sm grid place-items-center shrink-0">
        {n}
      </div>
      <div>
        <p className="font-semibold text-slate-900 text-sm">{title}</p>
        <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
      </div>
    </li>
  );
}

function QuickAction({
  to,
  label,
  Icon,
}: {
  to: string;
  label: string;
  Icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 rounded-xl px-3 py-2.5 hover:bg-brand-50 hover:text-brand-700 text-slate-700 transition group"
    >
      <Icon className="w-5 h-5 text-slate-400 group-hover:text-brand-600" />
      <span className="text-sm font-medium flex-1">{label}</span>
      <HiArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition" />
    </Link>
  );
}

function useGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}
