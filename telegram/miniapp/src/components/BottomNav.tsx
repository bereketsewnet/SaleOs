import { NavLink } from "react-router-dom";
import { cartCount, useCart } from "../store/cart";
import { withSearch } from "../lib/nav";

export function BottomNav() {
  const items = useCart((s) => s.items);
  const count = cartCount(items);
  return (
    <nav className="fixed bottom-0 inset-x-0 h-16 bg-tg-bg border-t border-black/10 grid grid-cols-3 z-40">
      <Tab to="/" label="Browse" icon="🛍️" />
      <Tab to="/cart" label="Cart" icon="🧺" badge={count > 0 ? count : undefined} />
      <Tab to="/info" label="Info" icon="ℹ️" />
    </nav>
  );
}

function Tab({
  to,
  label,
  icon,
  badge,
}: {
  to: string;
  label: string;
  icon: string;
  badge?: number;
}) {
  return (
    <NavLink
      to={withSearch(to)}
      end={to === "/"}
      className={({ isActive }) =>
        `flex flex-col items-center justify-center gap-0.5 text-xs ${
          isActive ? "text-tg-link" : "text-tg-hint"
        }`
      }
    >
      <span className="relative text-xl leading-none">
        {icon}
        {badge !== undefined && (
          <span className="absolute -top-1 -right-3 min-w-5 h-5 px-1 rounded-full bg-red-500 text-white text-[10px] font-semibold flex items-center justify-center">
            {badge}
          </span>
        )}
      </span>
      <span>{label}</span>
    </NavLink>
  );
}
