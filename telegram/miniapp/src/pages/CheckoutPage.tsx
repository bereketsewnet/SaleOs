import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import {
  HiOutlineUser,
  HiOutlinePhone,
  HiOutlineMapPin,
  HiOutlineDocumentText,
  HiOutlineShoppingBag,
  HiOutlineCheckBadge,
} from "react-icons/hi2";
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
      text: mutation.isPending ? "Placing order…" : `Place order · ETB ${total.toFixed(2)}`,
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
    <div className="p-4 pb-32 animate-fade-in">
      <h1 className="text-xl font-bold text-tg-text mb-3">Checkout</h1>

      <div className="card card-pad space-y-3">
        <Field label="Your name" Icon={HiOutlineUser}>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="input"
            placeholder="Abebe Bekele"
          />
        </Field>
        <Field label="Phone" Icon={HiOutlinePhone}>
          <input
            type="tel"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            className="input"
            placeholder="+251911000000"
          />
        </Field>
        <Field label="Delivery address" Icon={HiOutlineMapPin}>
          <textarea
            rows={2}
            value={form.address}
            onChange={(e) => setForm({ ...form, address: e.target.value })}
            className="input"
            placeholder="Bole, near Edna Mall"
          />
        </Field>
        <Field label="Notes (optional)" Icon={HiOutlineDocumentText}>
          <textarea
            rows={2}
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            className="input"
            placeholder="Anything we should know?"
          />
        </Field>
      </div>

      <div className="card card-pad mt-4">
        <h2 className="text-sm font-bold text-tg-text flex items-center gap-2 mb-2">
          <HiOutlineShoppingBag className="w-4 h-4 text-brand-600" /> Order summary
        </h2>
        {items.map((i) => (
          <div key={i.product_id} className="flex justify-between text-sm py-1">
            <span className="text-tg-text truncate pr-2">
              {i.title} <span className="text-tg-hint">× {i.quantity}</span>
            </span>
            <span className="text-tg-text font-medium whitespace-nowrap">
              ETB {(parseFloat(i.base_price || "0") * i.quantity).toFixed(2)}
            </span>
          </div>
        ))}
        <div className="border-t border-black/5 pt-2 mt-1 flex justify-between font-bold">
          <span>Total</span>
          <span className="text-brand-700">ETB {total.toFixed(2)}</span>
        </div>
      </div>

      {error && (
        <div className="mt-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-2xl px-3 py-2.5">
          {error}
        </div>
      )}

      <button
        onClick={() => mutation.mutate()}
        disabled={!canSubmit || mutation.isPending}
        className="btn-primary w-full mt-4"
      >
        <HiOutlineCheckBadge className="w-5 h-5" />
        {mutation.isPending ? "Placing order…" : `Place order · ETB ${total.toFixed(2)}`}
      </button>
    </div>
  );
}

function Field({
  label,
  Icon,
  children,
}: {
  label: string;
  Icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="text-xs font-semibold text-tg-hint mb-1.5 flex items-center gap-1.5">
        <Icon className="w-3.5 h-3.5" />
        {label}
      </label>
      {children}
    </div>
  );
}
