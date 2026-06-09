import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  listOrders,
  ORDER_STATUS_LABELS,
  type OrderStatus,
} from "../lib/ordersApi";

const STATUSES: OrderStatus[] = [
  "PENDING_PAYMENT",
  "PAYMENT_SUBMITTED",
  "PAYMENT_VERIFIED",
  "PAYMENT_REJECTED",
  "PREPARING",
  "SHIPPED",
  "DELIVERED",
  "CANCELLED",
];

export default function OrdersPage() {
  const [statusFilter, setStatusFilter] = useState<OrderStatus | "">("");

  const { data: orders = [], isLoading } = useQuery({
    queryKey: ["orders", statusFilter],
    queryFn: () =>
      listOrders(statusFilter ? { status_eq: statusFilter as OrderStatus } : undefined),
    refetchInterval: 30_000,
  });

  return (
    <div className="max-w-6xl">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-semibold text-slate-900">Orders</h1>
          <p className="text-slate-500">Real-time view of incoming orders from the Mini App + channel comments.</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        <FilterChip active={statusFilter === ""} onClick={() => setStatusFilter("")}>
          All
        </FilterChip>
        {STATUSES.map((s) => (
          <FilterChip
            key={s}
            active={statusFilter === s}
            onClick={() => setStatusFilter(s)}
          >
            {ORDER_STATUS_LABELS[s]}
          </FilterChip>
        ))}
      </div>

      {isLoading ? (
        <p className="text-slate-500">Loading…</p>
      ) : orders.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center">
          <p className="text-5xl mb-3">🧾</p>
          <h3 className="text-lg font-semibold text-slate-900 mb-1">No orders yet</h3>
          <p className="text-sm text-slate-500">
            Once a customer places an order from your Mini App, it'll appear here in real time.
          </p>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-2 text-left font-medium">Order</th>
                <th className="px-4 py-2 text-left font-medium">Customer</th>
                <th className="px-4 py-2 text-left font-medium">Channel</th>
                <th className="px-4 py-2 text-right font-medium">Total</th>
                <th className="px-4 py-2 text-left font-medium">Status</th>
                <th className="px-4 py-2 text-left font-medium">Receipt</th>
                <th className="px-4 py-2 text-left font-medium">When</th>
                <th></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {orders.map((o) => {
                const customer = (o.customer_info ?? {}) as { name?: string; phone?: string };
                return (
                  <tr key={o.id} className="hover:bg-slate-50">
                    <td className="px-4 py-2 font-mono text-xs">{o.id.slice(0, 8)}</td>
                    <td className="px-4 py-2">
                      <p className="font-medium">{customer.name ?? "—"}</p>
                      <p className="text-xs text-slate-500">{customer.phone ?? ""}</p>
                    </td>
                    <td className="px-4 py-2 text-xs">{o.channel_source}</td>
                    <td className="px-4 py-2 text-right font-semibold">ETB {o.total_amount}</td>
                    <td className="px-4 py-2">
                      <StatusBadge status={o.order_status} />
                    </td>
                    <td className="px-4 py-2">
                      {o.payment_proof_url ? (
                        <span className="text-xs text-emerald-700">📎 attached</span>
                      ) : (
                        <span className="text-xs text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-xs text-slate-500">
                      {new Date(o.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-right">
                      <Link
                        to={`/orders/${o.id}`}
                        className="text-xs font-medium text-brand-700"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`text-xs font-medium rounded-full px-3 py-1.5 border transition ${
        active
          ? "bg-brand-600 text-white border-brand-600"
          : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
      }`}
    >
      {children}
    </button>
  );
}

const STATUS_COLOR: Record<string, string> = {
  PENDING_PAYMENT: "bg-amber-100 text-amber-700",
  PAYMENT_SUBMITTED: "bg-amber-200 text-amber-800",
  PAYMENT_VERIFIED: "bg-emerald-100 text-emerald-700",
  PAYMENT_REJECTED: "bg-red-100 text-red-700",
  PREPARING: "bg-blue-100 text-blue-700",
  SHIPPED: "bg-indigo-100 text-indigo-700",
  DELIVERED: "bg-emerald-200 text-emerald-800",
  CANCELLED: "bg-slate-200 text-slate-700",
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded ${
        STATUS_COLOR[status] ?? "bg-slate-100 text-slate-700"
      }`}
    >
      {ORDER_STATUS_LABELS[status as OrderStatus] ?? status.replace(/_/g, " ")}
    </span>
  );
}
