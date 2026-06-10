import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  HiOutlineArrowLeft,
  HiOutlineCheck,
  HiOutlineXMark,
  HiOutlineUser,
  HiOutlinePhone,
  HiOutlineMapPin,
  HiOutlineCreditCard,
  HiOutlineDocumentText,
  HiOutlineCalendar,
  HiOutlineBanknotes,
  HiOutlineSparkles,
} from "react-icons/hi2";
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
  const fromComment = customer.source === "channel_comment";
  const awaitingReview = order.order_status === "PAYMENT_SUBMITTED";

  return (
    <div className="max-w-5xl mx-auto space-y-5 animate-fade-in">
      <Link
        to="/orders"
        className="inline-flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900 font-medium"
      >
        <HiOutlineArrowLeft className="w-4 h-4" /> Back to orders
      </Link>

      <div className="card card-pad flex flex-wrap items-center gap-4">
        <div className="w-12 h-12 rounded-2xl bg-brand-50 grid place-items-center text-brand-700 shrink-0">
          <HiOutlineDocumentText className="w-6 h-6" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900">
              Order #{order.id.slice(0, 8)}
            </h1>
            <span className="badge bg-slate-100 text-slate-600 uppercase">
              {order.channel_source}
            </span>
            <StatusBadge status={order.order_status as OrderStatus} />
          </div>
          <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
            <HiOutlineCalendar className="w-3.5 h-3.5" />
            {new Date(order.created_at).toLocaleString()}
          </p>
        </div>
      </div>

      {fromComment && (
        <div className="rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 text-sm flex items-start gap-2">
          <HiOutlineSparkles className="w-5 h-5 shrink-0 mt-0.5" />
          <p>Auto-created from a payment screenshot posted in the channel discussion group.</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card label="Total" Icon={HiOutlineBanknotes} tone="emerald">
          <p className="text-2xl font-bold text-slate-900">ETB {order.total_amount}</p>
        </Card>
        <Card label="Status" Icon={HiOutlineSparkles} tone="brand">
          {canEdit ? (
            <select
              value={order.order_status}
              onChange={(e) => statusMutation.mutate(e.target.value as OrderStatus)}
              disabled={statusMutation.isPending}
              className="input mt-0.5"
            >
              {ALL_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {ORDER_STATUS_LABELS[s]}
                </option>
              ))}
            </select>
          ) : (
            <p className="font-semibold text-slate-900">{ORDER_STATUS_LABELS[order.order_status as OrderStatus] ?? order.order_status}</p>
          )}
        </Card>
        <Card label="Placed" Icon={HiOutlineCalendar} tone="amber">
          <p className="text-sm font-medium text-slate-900">{new Date(order.created_at).toLocaleString()}</p>
        </Card>
      </div>

      <Timeline order={order} />

      <section className="card card-pad">
        <div className="flex items-start justify-between gap-3 mb-4 flex-wrap">
          <h2 className="section-title flex items-center gap-2">
            <HiOutlineCreditCard className="w-5 h-5 text-brand-600" />
            Payment receipt
          </h2>
          {awaitingReview && canEdit && (
            <div className="flex gap-2">
              <button
                onClick={() => verifyMutation.mutate()}
                disabled={verifyMutation.isPending}
                className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold px-3.5 py-2 rounded-xl shadow-sm disabled:opacity-50"
              >
                <HiOutlineCheck className="w-4 h-4" /> Verify payment
              </button>
              <button
                onClick={() => setShowRejectForm((v) => !v)}
                className="inline-flex items-center gap-1.5 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold px-3.5 py-2 rounded-xl shadow-sm"
              >
                <HiOutlineXMark className="w-4 h-4" /> Reject
              </button>
            </div>
          )}
        </div>

        {order.payment_proof_url ? (
          <a href={order.payment_proof_url} target="_blank" rel="noreferrer" className="block">
            <img
              src={order.payment_proof_url}
              alt="Payment receipt"
              className="max-h-96 rounded-xl ring-1 ring-slate-200 cursor-zoom-in shadow-sm"
            />
          </a>
        ) : (
          <p className="text-sm text-slate-500 italic">
            Customer hasn't uploaded a payment screenshot yet.
          </p>
        )}

        {order.payment_proof_uploaded_at && (
          <p className="text-xs text-slate-500 mt-3">
            Submitted: {new Date(order.payment_proof_uploaded_at).toLocaleString()}
          </p>
        )}
        {order.payment_verified_at && (
          <p className="text-xs text-emerald-700 mt-1 font-medium">
            ✓ Verified {new Date(order.payment_verified_at).toLocaleString()}
          </p>
        )}
        {order.payment_rejection_reason && (
          <p className="text-xs text-red-700 mt-1 font-medium">
            ✗ Rejected: {order.payment_rejection_reason}
          </p>
        )}

        {showRejectForm && (
          <div className="mt-4 border-t border-slate-200 pt-4">
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Reason (sent to customer): e.g. 'Receipt unreadable — please re-send a clearer photo'"
              rows={3}
              className="input"
            />
            <div className="mt-2 flex gap-2">
              <button
                onClick={() => rejectMutation.mutate(rejectReason)}
                disabled={!rejectReason.trim() || rejectMutation.isPending}
                className="btn-danger"
              >
                Send rejection
              </button>
              <button
                onClick={() => {
                  setShowRejectForm(false);
                  setRejectReason("");
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </section>

      <section className="card card-pad">
        <h2 className="section-title flex items-center gap-2 mb-3">
          <HiOutlineUser className="w-5 h-5 text-brand-600" /> Customer
        </h2>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          <Detail icon={<HiOutlineUser className="w-4 h-4" />} label="Name" value={customer.name ?? "—"} />
          <Detail icon={<HiOutlinePhone className="w-4 h-4" />} label="Phone" value={customer.phone ?? "—"} />
          <Detail
            icon={<HiOutlineMapPin className="w-4 h-4" />}
            label="Address"
            value={customer.address ?? "—"}
          />
          {customer.telegram_user_id ? (
            <Detail
              icon={<span>TG</span>}
              label="Telegram user id"
              value={String(customer.telegram_user_id)}
              mono
            />
          ) : null}
        </dl>
        {order.notes && (
          <div className="mt-4 rounded-xl bg-slate-50 border border-slate-200 px-3 py-2.5 text-sm text-slate-700">
            <p className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-1">Notes</p>
            {order.notes}
          </div>
        )}
      </section>

      <section className="card card-pad">
        <h2 className="section-title flex items-center gap-2 mb-3">
          <HiOutlineDocumentText className="w-5 h-5 text-brand-600" /> Items
        </h2>
        <ul className="divide-y divide-slate-100">
          {order.items.map((it) => (
            <li key={it.product_id} className="py-2.5 flex justify-between text-sm">
              <span className="font-medium text-slate-800">
                {it.title} <span className="text-slate-400">× {it.quantity}</span>
              </span>
              <span className="font-bold text-slate-900">ETB {it.line_total}</span>
            </li>
          ))}
        </ul>
      </section>

      {order.payment_account && (
        <section className="card card-pad">
          <h2 className="section-title flex items-center gap-2 mb-3">
            <HiOutlineBanknotes className="w-5 h-5 text-brand-600" />
            Payment account shown to customer
          </h2>
          <dl className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
            <Detail icon={null} label="Bank" value={order.payment_account.bank_name} />
            <Detail icon={null} label="Account" value={order.payment_account.account_number} mono />
            <Detail icon={null} label="Holder" value={order.payment_account.account_holder_name} />
          </dl>
        </section>
      )}
    </div>
  );
}

function Card({
  label,
  Icon,
  tone,
  children,
}: {
  label: string;
  Icon: React.ComponentType<{ className?: string }>;
  tone: "brand" | "emerald" | "amber";
  children: React.ReactNode;
}) {
  const tones: Record<string, { bg: string; fg: string }> = {
    brand: { bg: "bg-brand-50", fg: "text-brand-700" },
    emerald: { bg: "bg-emerald-50", fg: "text-emerald-700" },
    amber: { bg: "bg-amber-50", fg: "text-amber-700" },
  };
  const t = tones[tone];
  return (
    <div className="card card-pad">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs uppercase tracking-wider text-slate-500 font-semibold">{label}</p>
        <div className={`w-8 h-8 rounded-lg grid place-items-center ${t.bg}`}>
          <Icon className={`w-4 h-4 ${t.fg}`} />
        </div>
      </div>
      {children}
    </div>
  );
}

function Detail({
  icon,
  label,
  value,
  mono,
}: {
  icon: React.ReactNode | null;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wider text-slate-400 font-semibold flex items-center gap-1.5">
        {icon} {label}
      </dt>
      <dd className={`text-sm text-slate-900 mt-1 ${mono ? "font-mono" : "font-medium"}`}>{value}</dd>
    </div>
  );
}

const STATUS_BADGE: Record<string, string> = {
  PENDING_PAYMENT: "bg-amber-100 text-amber-700",
  PAYMENT_SUBMITTED: "bg-amber-200 text-amber-800",
  PAYMENT_VERIFIED: "bg-emerald-100 text-emerald-700",
  PAYMENT_REJECTED: "bg-red-100 text-red-700",
  PREPARING: "bg-blue-100 text-blue-700",
  SHIPPED: "bg-indigo-100 text-indigo-700",
  DELIVERED: "bg-emerald-200 text-emerald-800",
  CANCELLED: "bg-slate-200 text-slate-700",
};

function StatusBadge({ status }: { status: OrderStatus }) {
  return (
    <span
      className={`badge uppercase ${STATUS_BADGE[status] ?? "bg-slate-100 text-slate-700"}`}
    >
      {ORDER_STATUS_LABELS[status] ?? status}
    </span>
  );
}

function Timeline({ order }: { order: { order_status: string } }) {
  const currentIdx = ORDER_STATUS_FLOW.indexOf(order.order_status as OrderStatus);
  const isRejected = order.order_status === "PAYMENT_REJECTED";
  const isCancelled = order.order_status === "CANCELLED";
  return (
    <div className="card card-pad">
      <p className="text-xs uppercase tracking-wider text-slate-500 font-semibold mb-3">
        Status timeline
      </p>
      {isCancelled ? (
        <p className="text-sm text-red-700 font-semibold">This order was cancelled.</p>
      ) : (
        <ol className="flex flex-wrap items-center gap-1.5 text-xs">
          {ORDER_STATUS_FLOW.map((s, i) => {
            const isPast = i < currentIdx;
            const isCurrent = i === currentIdx;
            const cls = isPast
              ? "bg-emerald-100 text-emerald-800"
              : isCurrent
              ? isRejected
                ? "bg-red-100 text-red-800 ring-2 ring-red-300"
                : "bg-brand-100 text-brand-800 ring-2 ring-brand-300"
              : "bg-slate-100 text-slate-500";
            return (
              <li key={s} className="flex items-center gap-1.5">
                <span className={`px-2.5 py-1 rounded-full font-semibold uppercase tracking-wide ${cls}`}>
                  {ORDER_STATUS_LABELS[s]}
                </span>
                {i < ORDER_STATUS_FLOW.length - 1 && <span className="text-slate-300">→</span>}
              </li>
            );
          })}
        </ol>
      )}
      {isRejected && (
        <p className="text-sm text-red-700 mt-3 font-medium">
          Receipt was rejected — ask the customer to upload a new one.
        </p>
      )}
    </div>
  );
}
