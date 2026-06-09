import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getOrder,
  updateOrderStatus,
  verifyPayment,
  rejectPayment,
  type OrderStatus,
  ORDER_STATUS_LABELS,
  ORDER_STATUS_FLOW,
} from "../lib/ordersApi";
import { useHasRole } from "../components/RoleGate";

const ALL_STATUSES: OrderStatus[] = [
  "PENDING_PAYMENT",
  "PAYMENT_SUBMITTED",
  "PAYMENT_VERIFIED",
  "PAYMENT_REJECTED",
  "PREPARING",
  "SHIPPED",
  "DELIVERED",
  "CANCELLED",
];

export default function OrderDetailPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const canEdit = useHasRole(["ADMIN", "SUPER_ADMIN"]);
  const qc = useQueryClient();
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectForm, setShowRejectForm] = useState(false);

  const { data: order, isLoading } = useQuery({
    queryKey: ["order", orderId],
    queryFn: () => getOrder(orderId!),
    enabled: !!orderId,
    refetchInterval: 15000,
  });

  const statusMutation = useMutation({
    mutationFn: (status: OrderStatus) => updateOrderStatus(orderId!, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["order", orderId] });
      qc.invalidateQueries({ queryKey: ["orders"] });
    },
  });

  const verifyMutation = useMutation({
    mutationFn: () => verifyPayment(orderId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["order", orderId] });
      qc.invalidateQueries({ queryKey: ["orders"] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (reason: string) => rejectPayment(orderId!, reason),
    onSuccess: () => {
      setShowRejectForm(false);
      setRejectReason("");
      qc.invalidateQueries({ queryKey: ["order", orderId] });
      qc.invalidateQueries({ queryKey: ["orders"] });
    },
  });

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (!order) return <p className="text-slate-500">Order not found.</p>;

  const customer = (order.customer_info ?? {}) as {
    name?: string;
    phone?: string;
    address?: string;
    telegram_user_id?: number;
    source?: string;
  };
  const sourceLabel =
    customer.source === "channel_comment"
      ? "Auto-created from a payment screenshot posted in the channel discussion group"
      : null;
  const awaitingReview = order.order_status === "PAYMENT_SUBMITTED";

  return (
    <div className="max-w-4xl">
      <div className="mb-4">
        <Link to="/orders" className="text-sm text-slate-600 hover:text-slate-900">
          ← Back to orders
        </Link>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-4">
        <h1 className="text-2xl sm:text-3xl font-semibold text-slate-900">
          Order #{order.id.slice(0, 8)}
        </h1>
        <span className="text-xs font-semibold uppercase bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
          {order.channel_source}
        </span>
        <StatusBadge status={order.order_status as OrderStatus} />
      </div>

      {sourceLabel && (
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4">
          {sourceLabel}
        </p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card label="Total">
          <p className="text-2xl font-semibold">ETB {order.total_amount}</p>
        </Card>
        <Card label="Status">
          {canEdit ? (
            <select
              value={order.order_status}
              onChange={(e) => statusMutation.mutate(e.target.value as OrderStatus)}
              disabled={statusMutation.isPending}
              className="text-sm rounded-lg border border-slate-300 px-2 py-1.5 bg-white"
            >
              {ALL_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {ORDER_STATUS_LABELS[s]}
                </option>
              ))}
            </select>
          ) : (
            <p className="font-medium">{ORDER_STATUS_LABELS[order.order_status as OrderStatus] ?? order.order_status}</p>
          )}
        </Card>
        <Card label="Placed">
          <p className="text-sm">{new Date(order.created_at).toLocaleString()}</p>
        </Card>
      </div>

      <Timeline order={order} />

      <section className="bg-white border border-slate-200 rounded-2xl p-5 mb-4 mt-4">
        <div className="flex items-start justify-between gap-3 mb-3">
          <h2 className="font-semibold text-slate-900">Payment receipt</h2>
          {awaitingReview && canEdit && (
            <div className="flex gap-2">
              <button
                onClick={() => verifyMutation.mutate()}
                disabled={verifyMutation.isPending}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium disabled:opacity-50"
              >
                ✓ Verify payment
              </button>
              <button
                onClick={() => setShowRejectForm((v) => !v)}
                className="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium"
              >
                ✗ Reject
              </button>
            </div>
          )}
        </div>

        {order.payment_proof_url ? (
          <a
            href={order.payment_proof_url}
            target="_blank"
            rel="noreferrer"
            className="block"
          >
            <img
              src={order.payment_proof_url}
              alt="Payment receipt"
              className="max-h-96 rounded-lg border border-slate-200 cursor-zoom-in"
            />
          </a>
        ) : (
          <p className="text-sm text-slate-500 italic">
            Customer hasn't uploaded a payment screenshot yet.
          </p>
        )}

        {order.payment_proof_uploaded_at && (
          <p className="text-xs text-slate-500 mt-2">
            Submitted: {new Date(order.payment_proof_uploaded_at).toLocaleString()}
          </p>
        )}
        {order.payment_verified_at && (
          <p className="text-xs text-emerald-700 mt-1">
            Verified: {new Date(order.payment_verified_at).toLocaleString()}
          </p>
        )}
        {order.payment_rejection_reason && (
          <p className="text-xs text-red-700 mt-1">
            Rejected: {order.payment_rejection_reason}
          </p>
        )}

        {showRejectForm && (
          <div className="mt-3 border-t border-slate-200 pt-3">
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Reason (visible to customer): e.g. 'Receipt unreadable — please re-send a clearer photo'"
              rows={3}
              className="w-full text-sm rounded-lg border border-slate-300 px-3 py-2"
            />
            <div className="mt-2 flex gap-2">
              <button
                onClick={() => rejectMutation.mutate(rejectReason)}
                disabled={!rejectReason.trim() || rejectMutation.isPending}
                className="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium disabled:opacity-50"
              >
                Send rejection
              </button>
              <button
                onClick={() => {
                  setShowRejectForm(false);
                  setRejectReason("");
                }}
                className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </section>

      <section className="bg-white border border-slate-200 rounded-2xl p-5 mb-4">
        <h2 className="font-semibold text-slate-900 mb-2">Customer</h2>
        <p className="text-sm"><span className="text-slate-500">Name: </span>{customer.name ?? "—"}</p>
        <p className="text-sm"><span className="text-slate-500">Phone: </span>{customer.phone ?? "—"}</p>
        <p className="text-sm"><span className="text-slate-500">Address: </span>{customer.address ?? "—"}</p>
        {customer.telegram_user_id ? (
          <p className="text-sm text-slate-500">Telegram user id: {customer.telegram_user_id}</p>
        ) : null}
        {order.notes && (
          <p className="text-sm mt-2 bg-slate-50 border border-slate-200 rounded-lg p-2">
            <span className="text-slate-500">Notes: </span>{order.notes}
          </p>
        )}
      </section>

      <section className="bg-white border border-slate-200 rounded-2xl p-5 mb-4">
        <h2 className="font-semibold text-slate-900 mb-3">Items</h2>
        <ul className="divide-y divide-slate-100">
          {order.items.map((it) => (
            <li key={it.product_id} className="py-2 flex justify-between text-sm">
              <span>{it.title} × {it.quantity}</span>
              <span className="font-medium">ETB {it.line_total}</span>
            </li>
          ))}
        </ul>
      </section>

      {order.payment_account && (
        <section className="bg-white border border-slate-200 rounded-2xl p-5">
          <h2 className="font-semibold text-slate-900 mb-2">Payment account shown to customer</h2>
          <p className="text-sm"><span className="text-slate-500">Bank: </span>{order.payment_account.bank_name}</p>
          <p className="text-sm font-mono"><span className="text-slate-500">Account: </span>{order.payment_account.account_number}</p>
          <p className="text-sm"><span className="text-slate-500">Holder: </span>{order.payment_account.account_holder_name}</p>
        </section>
      )}
    </div>
  );
}

function Card({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4">
      <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">{label}</p>
      {children}
    </div>
  );
}

function StatusBadge({ status }: { status: OrderStatus }) {
  const tone =
    status === "PAYMENT_VERIFIED" || status === "DELIVERED" || status === "SHIPPED"
      ? "bg-emerald-100 text-emerald-800"
      : status === "PAYMENT_SUBMITTED"
      ? "bg-amber-100 text-amber-800"
      : status === "PAYMENT_REJECTED" || status === "CANCELLED"
      ? "bg-red-100 text-red-800"
      : "bg-slate-100 text-slate-700";
  return (
    <span className={`text-xs font-semibold uppercase px-2 py-0.5 rounded ${tone}`}>
      {ORDER_STATUS_LABELS[status] ?? status}
    </span>
  );
}

function Timeline({ order }: { order: { order_status: string } }) {
  const currentIdx = ORDER_STATUS_FLOW.indexOf(order.order_status as OrderStatus);
  const isRejected = order.order_status === "PAYMENT_REJECTED";
  const isCancelled = order.order_status === "CANCELLED";
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5">
      <p className="text-xs text-slate-500 uppercase tracking-wide mb-3">Status timeline</p>
      {isCancelled ? (
        <p className="text-sm text-red-700 font-medium">This order was cancelled.</p>
      ) : (
        <ol className="flex flex-wrap items-center gap-2 text-xs">
          {ORDER_STATUS_FLOW.map((s, i) => {
            const isPast = i < currentIdx;
            const isCurrent = i === currentIdx;
            const cls = isPast
              ? "bg-emerald-100 text-emerald-800"
              : isCurrent
              ? isRejected
                ? "bg-red-100 text-red-800"
                : "bg-amber-100 text-amber-800 ring-2 ring-amber-400"
              : "bg-slate-100 text-slate-500";
            return (
              <li key={s} className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded font-medium uppercase ${cls}`}>
                  {ORDER_STATUS_LABELS[s]}
                </span>
                {i < ORDER_STATUS_FLOW.length - 1 && (
                  <span className="text-slate-300">→</span>
                )}
              </li>
            );
          })}
        </ol>
      )}
      {isRejected && (
        <p className="text-sm text-red-700 mt-3">
          Receipt was rejected — ask the customer to upload a new one.
        </p>
      )}
    </div>
  );
}
