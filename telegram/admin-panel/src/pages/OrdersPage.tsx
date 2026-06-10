import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  HiOutlineDocumentText,
  HiOutlinePaperClip,
  HiOutlineArrowTopRightOnSquare,
} from "react-icons/hi2";
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
    <div className="max-w-7xl mx-auto space-y-5 animate-fade-in">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">Orders</h1>
        <p className="text-slate-500 text-sm mt-1">
          Real-time stream of orders from the Mini App and channel comments.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
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
        <div className="card card-pad p-10 text-center">
          <div className="w-16 h-16 rounded-2xl bg-brand-50 grid place-items-center text-brand-600 mx-auto mb-4">
            <HiOutlineDocumentText className="w-9 h-9" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-1">No orders yet</h3>
          <p className="text-sm text-slate-500 max-w-sm mx-auto">
            Once a customer places an order from your Mini App or sends a receipt in your
            channel comments, it'll appear here in real time.
          </p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50/80 text-slate-600 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">Order</th>
                  <th className="px-4 py-3 text-left font-semibold">Customer</th>
                  <th className="px-4 py-3 text-left font-semibold">Channel</th>
                  <th className="px-4 py-3 text-right font-semibold">Total</th>
                  <th className="px-4 py-3 text-left font-semibold">Status</th>
                  <th className="px-4 py-3 text-left font-semibold">Receipt</th>
                  <th className="px-4 py-3 text-left font-semibold">When</th>
                  <th></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {orders.map((o) => {
                  const customer = (o.customer_info ?? {}) as { name?: string; phone?: string };
                  return (
                    <tr key={o.id} className="hover:bg-brand-50/30 transition">
                      <td className="px-4 py-3 font-mono text-xs text-slate-700">
                        #{o.id.slice(0, 8)}
                      </td>
                      <td className="px-4 py-3">
                        <p className="font-semibold text-slate-900">{customer.name ?? "—"}</p>
                        <p className="text-xs text-slate-500">{customer.phone ?? ""}</p>
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500">{o.channel_source}</td>
                      <td className="px-4 py-3 text-right font-bold text-slate-900">
                        ETB {o.total_amount}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={o.order_status} />
                      </td>
                      <td className="px-4 py-3">
                        {o.payment_proof_url ? (
                          <span className="inline-flex items-center gap-1 text-xs text-emerald-700 font-medium">
                            <HiOutlinePaperClip className="w-3.5 h-3.5" /> attached
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500">
                        {new Date(o.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          to={`/orders/${o.id}`}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-brand-700 hover:text-brand-800"
                        >
                          View <HiOutlineArrowTopRightOnSquare className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
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
      className={`text-xs font-semibold rounded-full px-3 py-1.5 border transition ${
        active
          ? "bg-brand-600 text-white border-brand-600 shadow-sm"
          : "bg-white text-slate-700 border-slate-200 hover:border-brand-400 hover:text-brand-700"
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
      className={`text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full ${
        STATUS_COLOR[status] ?? "bg-slate-100 text-slate-700"
      }`}
    >
      {ORDER_STATUS_LABELS[status as OrderStatus] ?? status.replace(/_/g, " ")}
    </span>
  );
}
