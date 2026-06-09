import { Link, useNavigate } from "react-router-dom";
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
      <div className="p-6 text-center mt-16">
        <p className="text-5xl">🧺</p>
        <h2 className="text-lg font-semibold mt-3">Your cart is empty</h2>
        <Link
          to={withSearch("/")}
          className="mt-4 inline-block rounded-xl bg-tg-button text-tg-buttonText font-medium px-4 py-2.5 text-sm"
        >
          Browse products
        </Link>
      </div>
    );
  }

  return (
    <div className="p-4 pb-32">
      <h1 className="text-lg font-semibold mb-3">Your cart</h1>
      <ul className="space-y-3">
        {items.map((it) => (
          <li key={it.product_id} className="flex gap-3 items-start bg-tg-secondaryBg rounded-2xl p-3">
            <div className="w-16 h-16 bg-black/10 rounded-lg overflow-hidden flex items-center justify-center">
              {it.image_url ? (
                <img src={it.image_url} alt={it.title} className="w-full h-full object-cover" />
              ) : (
                <span>📦</span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium line-clamp-1">{it.title}</p>
              <p className="text-sm font-semibold">ETB {it.base_price}</p>
              <div className="mt-2 flex items-center gap-2">
                <button
                  onClick={() => setQuantity(it.product_id, it.quantity - 1)}
                  className="w-7 h-7 rounded-full bg-black/10 text-base"
                >
                  −
                </button>
                <span className="text-sm w-6 text-center">{it.quantity}</span>
                <button
                  onClick={() => setQuantity(it.product_id, it.quantity + 1)}
                  className="w-7 h-7 rounded-full bg-black/10 text-base"
                >
                  +
                </button>
                <button
                  onClick={() => removeItem(it.product_id)}
                  className="ml-auto text-xs text-red-600"
                >
                  Remove
                </button>
              </div>
            </div>
          </li>
        ))}
      </ul>

      <div className="fixed bottom-16 inset-x-0 px-4 py-3 bg-tg-bg border-t border-black/10">
        <div className="flex items-center justify-between mb-2">
          <span className="text-tg-hint text-sm">Total</span>
          <span className="font-semibold">ETB {total.toFixed(2)}</span>
        </div>
        <button
          onClick={() => navigate(withSearch("/checkout"))}
          className="w-full py-3 rounded-xl bg-tg-button text-tg-buttonText font-semibold text-sm"
        >
          Checkout
        </button>
      </div>
    </div>
  );
}
