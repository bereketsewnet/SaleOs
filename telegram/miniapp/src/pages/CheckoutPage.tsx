import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { cartTotal, useCart } from "../store/cart";
import { placeOrder } from "../lib/catalogApi";
import { hapticNotification, useMainButton, clearMainButton } from "../lib/telegram";
import { withSearch } from "../lib/nav";

export default function CheckoutPage() {
  const items = useCart((s) => s.items);
  const clear = useCart((s) => s.clear);
  const navigate = useNavigate();
  const total = cartTotal(items);

  const [form, setForm] = useState({ name: "", phone: "", address: "", notes: "" });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      placeOrder({
        items: items.map((i) => ({ product_id: i.product_id, quantity: i.quantity })),
        customer: { name: form.name, phone: form.phone, address: form.address },
        notes: form.notes || null,
      }),
    onSuccess: (order) => {
      hapticNotification("success");
      clear();
      navigate({ ...withSearch(`/order/${order.id}/success`) }, { replace: true });
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      if (detail?.error === "out_of_stock") {
        setError("Sorry — one of the items is out of stock. Please adjust your cart.");
      } else if (detail?.error === "product_not_found") {
        setError("Item no longer available.");
      } else {
        setError("Couldn't place your order. Please try again.");
      }
      hapticNotification("error");
    },
  });

  const canSubmit =
    items.length > 0 &&
    form.name.trim().length >= 1 &&
    form.phone.trim().length >= 4 &&
    form.address.trim().length >= 1;

  useEffect(() => {
    if (items.length === 0) return;
    useMainButton({
      text: mutation.isPending
        ? "Placing order…"
        : `Place order · ETB ${total.toFixed(2)}`,
      onClick: () => mutation.mutate(),
      enabled: canSubmit && !mutation.isPending,
      loading: mutation.isPending,
    });
    return () => clearMainButton();
  }, [canSubmit, mutation.isPending, total, items.length]);

  if (items.length === 0) {
    return <p className="p-6 text-center text-tg-hint">Your cart is empty.</p>;
  }

  return (
    <div className="p-4 pb-32">
      <h1 className="text-lg font-semibold mb-3">Checkout</h1>

      <div className="space-y-3">
        <Field label="Your name">
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className={inputCls}
            placeholder="Abebe Bekele"
          />
        </Field>
        <Field label="Phone">
          <input
            type="tel"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            className={inputCls}
            placeholder="+251911000000"
          />
        </Field>
        <Field label="Delivery address">
          <textarea
            rows={2}
            value={form.address}
            onChange={(e) => setForm({ ...form, address: e.target.value })}
            className={inputCls}
            placeholder="Bole, near Edna Mall"
          />
        </Field>
        <Field label="Notes (optional)">
          <textarea
            rows={2}
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            className={inputCls}
            placeholder="Anything we should know?"
          />
        </Field>
      </div>

      <div className="mt-5 bg-tg-secondaryBg rounded-2xl p-3 space-y-2">
        <h2 className="text-sm font-semibold">Order summary</h2>
        {items.map((i) => (
          <div key={i.product_id} className="flex justify-between text-sm">
            <span className="truncate">{i.title} × {i.quantity}</span>
            <span>ETB {(parseFloat(i.base_price || "0") * i.quantity).toFixed(2)}</span>
          </div>
        ))}
        <div className="border-t border-black/10 pt-2 flex justify-between font-semibold">
          <span>Total</span>
          <span>ETB {total.toFixed(2)}</span>
        </div>
      </div>

      {error && (
        <div className="mt-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      {/* Fallback button for browsers without Telegram MainButton */}
      <button
        onClick={() => mutation.mutate()}
        disabled={!canSubmit || mutation.isPending}
        className="mt-4 w-full py-3 rounded-xl bg-tg-button text-tg-buttonText font-semibold disabled:opacity-50"
      >
        {mutation.isPending ? "Placing order…" : `Place order · ETB ${total.toFixed(2)}`}
      </button>
    </div>
  );
}

const inputCls =
  "w-full rounded-xl bg-tg-secondaryBg px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-tg-link/50";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs text-tg-hint mb-1">{label}</label>
      {children}
    </div>
  );
}
