import { useAuthStore } from "../store/auth";

export default function DashboardHome() {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl sm:text-3xl font-semibold text-slate-900 mb-1">
        Welcome back, {user?.first_name} 👋
      </h1>
      <p className="text-slate-500 mb-6">
        Here's an overview of your business on SaleOS.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat title="Orders today" value="0" />
        <Stat title="Revenue today" value="ETB 0" />
        <Stat title="Products live" value="0" />
        <Stat title="Pending reviews" value="0" />
      </div>

      <section className="mt-8 bg-white border border-slate-200 rounded-2xl p-5 sm:p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-2">Getting started</h2>
        <ol className="list-decimal pl-5 space-y-1.5 text-slate-700">
          <li>Add your Telegram bot token in <span className="font-medium">Settings → Telegram</span>.</li>
          <li>Add your bank account details (used for customer payments).</li>
          <li>Create your first product.</li>
          <li>Connect your Telegram channel.</li>
        </ol>
      </section>
    </div>
  );
}

function Stat({ title, value }: { title: string; value: string }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{title}</p>
      <p className="text-2xl font-semibold text-slate-900 mt-1">{value}</p>
    </div>
  );
}
