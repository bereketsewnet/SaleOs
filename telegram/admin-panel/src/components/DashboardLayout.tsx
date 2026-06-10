import { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  HiOutlineCube,
  HiOutlineCog6Tooth,
  HiOutlineDocumentText,
  HiOutlineHome,
  HiOutlineBars3,
  HiOutlineXMark,
  HiOutlineArrowRightOnRectangle,
  HiOutlineSparkles,
} from "react-icons/hi2";
import { useAuthStore } from "../store/auth";
import { logout as apiLogout } from "../lib/authApi";

type NavItem = {
  to: string;
  label: string;
  Icon: React.ComponentType<{ className?: string }>;
};

const NAV: NavItem[] = [
  { to: "/", label: "Dashboard", Icon: HiOutlineHome },
  { to: "/products", label: "Products", Icon: HiOutlineCube },
  { to: "/orders", label: "Orders", Icon: HiOutlineDocumentText },
  { to: "/settings", label: "Settings", Icon: HiOutlineCog6Tooth },
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
    <div className="app-shell bg-[#f5f9fc]">
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-30 md:hidden animate-fade-in"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar — fixed/sticky, only main content scrolls */}
      <aside
        className={`fixed md:relative inset-y-0 left-0 z-40 w-72 md:w-64 shrink-0 bg-white border-r border-slate-200/80 transform transition-transform duration-300 md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="h-16 flex items-center justify-between px-5 border-b border-slate-200/80">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 grid place-items-center text-white shadow-sm">
              <HiOutlineSparkles className="w-5 h-5" />
            </div>
            <div className="flex flex-col leading-tight">
              <span className="text-base font-bold text-slate-900">SaleOS</span>
              <span className="text-[10px] uppercase tracking-wider text-slate-500">
                Telegram suite
              </span>
            </div>
          </Link>
          <button
            className="md:hidden p-1.5 rounded-lg text-slate-500 hover:bg-slate-100"
            onClick={() => setOpen(false)}
            aria-label="Close sidebar"
          >
            <HiOutlineXMark className="w-5 h-5" />
          </button>
        </div>

        <nav className="p-3 space-y-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition group ${
                  isActive
                    ? "bg-brand-50 text-brand-700 shadow-sm"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.Icon
                    className={`w-5 h-5 transition ${
                      isActive ? "text-brand-600" : "text-slate-400 group-hover:text-slate-600"
                    }`}
                  />
                  <span>{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 inset-x-0 p-3 border-t border-slate-200/80 bg-white">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-600 hover:bg-red-50 hover:text-red-700 transition"
          >
            <HiOutlineArrowRightOnRectangle className="w-5 h-5" />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex flex-col flex-1 min-w-0">
        <header className="h-16 bg-white/80 backdrop-blur-md border-b border-slate-200/80 flex items-center justify-between px-4 sm:px-6 sticky top-0 z-20">
          <button
            className="md:hidden p-2 rounded-lg text-slate-700 hover:bg-slate-100"
            onClick={() => setOpen(true)}
            aria-label="Open sidebar"
          >
            <HiOutlineBars3 className="w-6 h-6" />
          </button>

          <div className="flex items-center gap-3 ml-auto">
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-sm font-semibold text-slate-900">
                {user?.first_name} {user?.last_name}
              </span>
              <span className="text-xs text-slate-500 capitalize">
                {user?.role?.toLowerCase().replace("_", " ")}
              </span>
            </div>
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-white grid place-items-center font-semibold shadow-sm">
              {user?.first_name?.[0]?.toUpperCase() ?? "?"}
            </div>
          </div>
        </header>

        <main className="app-main p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
