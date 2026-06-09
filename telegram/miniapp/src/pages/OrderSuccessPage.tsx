import { useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getOrder, uploadPaymentProof, type Order } from "../lib/catalogApi";
import { withSearch } from "../lib/nav";
import { hapticImpact, hapticNotification } from "../lib/telegram";

const STATUS_LABELS: Record<string, string> = {
  PENDING_PAYMENT: "Awaiting your payment",
  PAYMENT_SUBMITTED: "Receipt received — verifying",
  PAYMENT_VERIFIED: "Payment confirmed",
  PAYMENT_REJECTED: "Receipt rejected — please re-upload",
  PREPARING: "Preparing your order",
  SHIPPED: "Out for delivery",
  DELIVERED: "Delivered",
  CANCELLED: "Cancelled",
};

const STATUS_TONE: Record<string, string> = {
  PENDING_PAYMENT: "bg-amber-50 text-amber-800 border-amber-200",
  PAYMENT_SUBMITTED: "bg-amber-50 text-amber-900 border-amber-300",
  PAYMENT_VERIFIED: "bg-emerald-50 text-emerald-800 border-emerald-200",
  PAYMENT_REJECTED: "bg-red-50 text-red-800 border-red-200",
  PREPARING: "bg-blue-50 text-blue-800 border-blue-200",
  SHIPPED: "bg-indigo-50 text-indigo-800 border-indigo-200",
  DELIVERED: "bg-emerald-50 text-emerald-900 border-emerald-300",
  CANCELLED: "bg-slate-100 text-slate-700 border-slate-300",
};

export default function OrderSuccessPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const qc = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const { data: order, isLoading } = useQuery({
    queryKey: ["order", orderId],
    queryFn: () => getOrder(orderId!),
    enabled: !!orderId,
    refetchInterval: 15000,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadPaymentProof(orderId!, file),
    onSuccess: (fresh) => {
      qc.setQueryData(["order", orderId], fresh);
      setUploadError(null);
      hapticNotification("success");
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      const message =
        typeof detail === "string" ? detail : detail?.error ?? "Upload failed — try again";
      setUploadError(String(message));
      hapticNotification("error");
    },
  });

  if (isLoading) return <p className="p-6 text-tg-hint">Loading…</p>;
  if (!order) return <p className="p-6 text-tg-hint">Order not found.</p>;

  const tgUsername = order.dm_contacts.find((c) => c.kind === "TELEGRAM_USERNAME");
  const phone = order.dm_contacts.find((c) => c.kind === "PHONE");
  const confirmTarget = tgUsername || phone;

  const hasProof = !!order.payment_proof_url;
  const needsUpload =
    order.order_status === "PENDING_PAYMENT" || order.order_status === "PAYMENT_REJECTED";

  function pickFile() {
    hapticImpact("light");
    fileInputRef.current?.click();
  }

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 8 * 1024 * 1024) {
      setUploadError("File too large — max 8 MB");
      return;
    }
    setUploadError(null);
    uploadMutation.mutate(file);
    e.target.value = "";
  }

  return (
    <div className="p-4 pb-24">
      <div className="text-center mt-2">
        <div className="text-5xl">{hasProof ? "🧾" : "✅"}</div>
        <h1 className="text-xl font-semibold mt-2">
          {hasProof ? "Receipt received" : "Order placed!"}
        </h1>
        <p className="text-sm text-tg-hint">
          Order #{order.id.slice(0, 8)} · Total <span className="font-semibold">ETB {order.total_amount}</span>
        </p>
      </div>

      <StatusBanner order={order} />

      {order.payment_account ? (
        <section className="mt-5 bg-tg-secondaryBg rounded-2xl p-4">
          <h2 className="font-semibold mb-2">💳 Pay to this account</h2>
          <p className="text-sm">
            <span className="text-tg-hint">Bank: </span>
            <span className="font-medium">{order.payment_account.bank_name}</span>
          </p>
          <p className="text-sm">
            <span className="text-tg-hint">Account: </span>
            <span className="font-mono font-semibold">{order.payment_account.account_number}</span>
          </p>
          <p className="text-sm">
            <span className="text-tg-hint">Name: </span>
            <span className="font-medium">{order.payment_account.account_holder_name}</span>
          </p>
        </section>
      ) : (
        <section className="mt-5 bg-yellow-50 border border-yellow-200 rounded-2xl p-4 text-sm">
          The shop hasn't set up a payment account yet. Please reach out using a contact below.
        </section>
      )}

      <section className="mt-4 bg-tg-secondaryBg rounded-2xl p-4">
        <h2 className="font-semibold mb-2">📸 Upload your payment screenshot</h2>
        <p className="text-xs text-tg-hint mb-3">
          {needsUpload
            ? "After paying, send the receipt here. The shop will verify and confirm your order."
            : "Your receipt is uploaded. You'll see the status update here once it's verified."}
        </p>

        {hasProof && (
          <a
            href={order.payment_proof_url!}
            target="_blank"
            rel="noreferrer"
            className="block mb-3"
          >
            <img
              src={order.payment_proof_url!}
              alt="Your receipt"
              className="max-h-64 rounded-lg border border-black/10"
            />
          </a>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleFile}
        />
        <button
          onClick={pickFile}
          disabled={uploadMutation.isPending}
          className="w-full rounded-xl bg-tg-button text-tg-buttonText font-semibold py-3 disabled:opacity-50"
        >
          {uploadMutation.isPending
            ? "Uploading…"
            : hasProof
            ? "Replace receipt"
            : "Upload receipt"}
        </button>
        {uploadError && (
          <p className="text-xs text-red-600 mt-2">{uploadError}</p>
        )}
      </section>

      {confirmTarget && (
        <section className="mt-4 bg-tg-secondaryBg rounded-2xl p-4">
          <h2 className="font-semibold mb-1">Need help? Reach us at:</h2>
          <p className="text-sm">
            {confirmTarget.kind === "TELEGRAM_USERNAME" ? (
              <a
                href={`https://t.me/${confirmTarget.value.replace(/^@/, "")}`}
                target="_blank"
                rel="noreferrer"
                className="text-tg-link font-medium underline"
              >
                {confirmTarget.value}
              </a>
            ) : (
              <a href={`tel:${confirmTarget.value}`} className="text-tg-link font-medium">
                {confirmTarget.value}
              </a>
            )}
            {confirmTarget.label && (
              <span className="text-tg-hint"> · {confirmTarget.label}</span>
            )}
          </p>
        </section>
      )}

      <Link
        to={withSearch("/")}
        className="mt-6 block text-center rounded-xl bg-tg-secondaryBg font-semibold py-3"
      >
        Continue shopping
      </Link>
    </div>
  );
}

function StatusBanner({ order }: { order: Order }) {
  const label = STATUS_LABELS[order.order_status] ?? order.order_status;
  const tone = STATUS_TONE[order.order_status] ?? "bg-tg-secondaryBg border-black/10";
  return (
    <section className={`mt-4 rounded-2xl border p-3 text-sm ${tone}`}>
      <p className="font-semibold">{label}</p>
      {order.order_status === "PAYMENT_REJECTED" && order.payment_rejection_reason && (
        <p className="mt-1 text-xs">Reason: {order.payment_rejection_reason}</p>
      )}
      {order.payment_proof_uploaded_at && (
        <p className="mt-1 text-xs opacity-80">
          Receipt sent {new Date(order.payment_proof_uploaded_at).toLocaleString()}
        </p>
      )}
    </section>
  );
}
