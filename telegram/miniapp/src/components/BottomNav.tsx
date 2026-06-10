import { NavLink } from "react-router-dom";
import {
  HiOutlineShoppingBag,
  HiShoppingBag,
  HiOutlineShoppingCart,
  HiShoppingCart,
  HiOutlineInformationCircle,
  HiInformationCircle,
} from "react-icons/hi2";
import { cartCount, useCart } from "../store/cart";
import { withSearch } from "../lib/nav";

type IconCmp = React.ComponentType<{ className?: string }>;

export function BottomNav() {
  const items = useCart((s) => s.items);
  const count = cartCount(items);
  return (
    <nav className="fixed bottom-0 inset-x-0 z-40 bg-tg-bg/90 backdrop-blur-xl border-t border-black/5 grid grid-cols-3 pt-1.5 pb-[max(env(safe-area-inset-bottom),0.5rem)]">
      <Tab to="/" label="Browse" Icon={HiOutlineShoppingBag} IconActive={HiShoppingBag} />
      <Tab
        to="/cart"
        label="Cart"
        Icon={HiOutlineShoppingCart}
        IconActive={HiShoppingCart}
        badge={count > 0 ? count : undefined}
      />
      <Tab
        to="/info"
        label="Info"
        Icon={HiOutlineInformationCircle}
        IconActive={HiInformationCircle}
      />
    </nav>
  );
}

function Tab({
  to,
  label,
  Icon,
  IconActive,
  badge,
}: {
  to: string;
  label: string;
  Icon: IconCmp;
  IconActive: IconCmp;
  badge?: number;
}) {
  return (
    <NavLink
      to={withSearch(to)}
      end={to === "/"}
      className={({ isActive }) =>
        `flex flex-col items-center justify-center gap-0.5 text-[11px] font-medium transition ${
          isActive ? "text-brand-600" : "text-tg-hint hover:text-slate-700"
        }`
      }
    >
      {({ isActive }) => {
        const I = isActive ? IconActive : Icon;
        return (
          <>
            <span className="relative">
              <I className={`w-6 h-6 transition ${isActive ? "scale-110" : ""}`} />
              {badge !== undefined && (
                <span className="absolute -top-1 -right-2.5 min-w-[18px] h-[18px] px-1 rounded-full bg-red-500 text-white text-[10px] font-bold leading-[18px] text-center ring-2 ring-tg-bg">
                  {badge}
                </span>
              )}
            </span>
            <span>{label}</span>
          </>
        );
      }}
    </NavLink>
  );
}
