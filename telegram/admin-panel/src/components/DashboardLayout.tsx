import { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/auth";
import { logout as apiLogout } from "../lib/authApi";

const NAV = [
  { to: "/", label: "Dashboard", icon: "🏠" },
  { to: "/products", label: "Products", icon: "📦" },
  { to: "/orders", label: "Orders", icon: "🧾" },
  { to: "/bot", label: "Telegram Bot", icon: "🤖" },
  { to: "/settings", label: "Settings", icon: "⚙️" },
];

export function DashboardLayout() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const clear = useAuthStore((s) => s.clear);

  async function handleLogout() {
    try {
      await apiLogout();
    } catch {
      // ignore — still clear locally
    }
    clear();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/40 z-30 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-40 w-64 bg-white border-r border-slate-200 transform transition-transform md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="h-16 flex items-center px-5 border-b border-slate-200">
          <Link to="/" className="text-lg font-semibold text-slate-900">
            SaleOS
          </Link>
        </div>
        <nav className="p-3 space-y-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-700 hover:bg-slate-100"
                }`
              }
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main column */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 sm:px-6">
          <button
            className="md:hidden p-2 rounded-lg hover:bg-slate-100"
            onClick={() => setOpen(true)}
            aria-label="Open sidebar"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>

          <div className="flex items-center gap-3 ml-auto">
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-sm font-medium text-slate-900">
                {user?.first_name} {user?.last_name}
              </span>
              <span className="text-xs text-slate-500">{user?.role}</span>
            </div>
            <div className="w-9 h-9 rounded-full bg-brand-600 text-white flex items-center justify-center font-semibold">
              {user?.first_name?.[0] ?? "?"}
            </div>
            <button
              onClick={handleLogout}
              className="text-sm text-slate-600 hover:text-slate-900 px-3 py-1.5 rounded-lg hover:bg-slate-100"
            >
              Sign out
            </button>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
