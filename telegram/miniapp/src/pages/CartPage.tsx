import { Link, useNavigate } from "react-router-dom";
import {
  HiOutlineShoppingCart,
  HiOutlineCube,
  HiOutlinePlus,
  HiOutlineMinus,
  HiOutlineTrash,
  HiOutlineArrowRight,
} from "react-icons/hi2";
import { cartTotal, useCart } from "../store/cart";
import { withSearch } from "../lib/nav";

export default function CartPage() {
  const items = useCart((s) => s.items);
  const setQuantity = useCart((s) => s.setQuantity);
  const removeItem = useCart((s) => s.removeItem);
  const navigate = useNavigate();
  const total = cartTotal(items);

  if (items.length === 0) {
    return (
      <div className="p-6 text-center mt-12 animate-fade-in">
        <div className="w-20 h-20 rounded-3xl bg-brand-50 grid place-items-center text-brand-600 mx-auto mb-4">
          <HiOutlineShoppingCart className="w-10 h-10" />
        </div>
        <h2 className="text-lg font-bold text-tg-text">Your cart is empty</h2>
        <p className="text-sm text-tg-hint mt-1">Add a product to start checkout.</p>
        <Link to={withSearch("/")} className="btn-primary mt-5 inline-flex">
          Browse products <HiOutlineArrowRight className="w-4 h-4" />
        </Link>
      </div>
    );
  }

  return (
    <div className="p-4 pb-40 animate-fade-in">
      <h1 className="text-xl font-bold text-tg-text mb-3">Your cart</h1>
      <ul className="space-y-3">
        {items.map((it) => (
          <li key={it.product_id} className="card p-3 flex gap-3 items-start animate-slide-up">
            <div className="w-16 h-16 bg-tg-secondaryBg rounded-2xl overflow-hidden grid place-items-center shrink-0">
              {it.image_url ? (
                <img src={it.image_url} alt={it.title} className="w-full h-full object-cover" />
              ) : (
                <HiOutlineCube className="w-6 h-6 text-tg-hint" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-tg-text line-clamp-1">{it.title}</p>
              <p className="text-sm font-bold text-brand-700 mt-0.5">ETB {it.base_price}</p>
              <div className="mt-2 flex items-center gap-1.5">
                <Stepper onClick={() => setQuantity(it.product_id, it.quantity - 1)}>
                  <HiOutlineMinus className="w-3.5 h-3.5" />
                </Stepper>
                <span className="text-sm font-semibold w-7 text-center">{it.quantity}</span>
                <Stepper onClick={() => setQuantity(it.product_id, it.quantity + 1)}>
                  <HiOutlinePlus className="w-3.5 h-3.5" />
                </Stepper>
                <button
                  onClick={() => removeItem(it.product_id)}
                  className="ml-auto inline-flex items-center gap-1 text-xs font-medium text-red-600 hover:text-red-700"
                >
                  <HiOutlineTrash className="w-3.5 h-3.5" /> Remove
                </button>
              </div>
            </div>
          </li>
        ))}
      </ul>

      <div className="fixed bottom-[68px] inset-x-0 z-30 px-4 py-3 bg-tg-bg/95 backdrop-blur-xl border-t border-black/5">
        <div className="max-w-md mx-auto">
          <div className="flex items-center justify-between mb-2">
            <span className="text-tg-hint text-sm">Total</span>
            <span className="text-xl font-bold text-tg-text">ETB {total.toFixed(2)}</span>
          </div>
          <button onClick={() => navigate(withSearch("/checkout"))} className="btn-primary w-full">
            Checkout <HiOutlineArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function Stepper({ onClick, children }: { onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className="w-7 h-7 rounded-full bg-tg-secondaryBg text-slate-700 grid place-items-center hover:bg-slate-200 active:scale-90 transition"
    >
      {children}
    </button>
  );
}
