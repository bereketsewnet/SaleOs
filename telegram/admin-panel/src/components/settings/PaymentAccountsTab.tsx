import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createPaymentAccount,
  deletePaymentAccount,
  listPaymentAccounts,
  updatePaymentAccount,
  type PaymentAccount,
  type PaymentAccountCreate,
} from "../../lib/paymentAccountsApi";
import { useHasRole } from "../RoleGate";

const EMPTY_FORM: PaymentAccountCreate = {
  bank_name: "",
  account_number: "",
  account_holder_name: "",
  phone: "",
};

export function PaymentAccountsTab() {
  const canEdit = useHasRole(["ADMIN"]);
  const qc = useQueryClient();

  const { data: accounts = [], isLoading } = useQuery({
    queryKey: ["paymentAccounts"],
    queryFn: listPaymentAccounts,
  });

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<PaymentAccountCreate>(EMPTY_FORM);

  const createMutation = useMutation({
    mutationFn: createPaymentAccount,
    onSuccess: () => {
      setForm(EMPTY_FORM);
      setShowForm(false);
      qc.invalidateQueries({ queryKey: ["paymentAccounts"] });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      updatePaymentAccount(id, { is_active: isActive }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["paymentAccounts"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: deletePaymentAccount,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["paymentAccounts"] }),
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    createMutation.mutate(form);
  }

  function update<K extends keyof PaymentAccountCreate>(k: K, v: string) {
    setForm((prev) => ({ ...prev, [k]: v }));
  }

  if (isLoading) return <p className="text-slate-500">Loading…</p>;

  return (
    <div className="space-y-4">
      {!canEdit && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm px-3 py-2">
          You're in read-only mode. Only ADMIN can change payment accounts.
        </div>
      )}

      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-600">
          {accounts.length === 0
            ? "No accounts yet. Add one so customers know where to pay."
            : `${accounts.length} account${accounts.length === 1 ? "" : "s"}`}
        </p>
        {canEdit && !showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="text-sm rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium px-3 py-1.5"
          >
            + Add account
          </button>
        )}
      </div>

      {canEdit && showForm && (
        <form
          onSubmit={onSubmit}
          className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4"
        >
          <Field label="Bank name" required>
            <input
              required
              className={inputClass}
              value={form.bank_name}
              onChange={(e) => update("bank_name", e.target.value)}
              placeholder="Commercial Bank of Ethiopia"
            />
          </Field>
          <Field label="Account number" required>
            <input
              required
              className={inputClass}
              value={form.account_number}
              onChange={(e) => update("account_number", e.target.value)}
              placeholder="1000123456789"
            />
          </Field>
          <Field label="Account holder name" required>
            <input
              required
              className={inputClass}
              value={form.account_holder_name}
              onChange={(e) => update("account_holder_name", e.target.value)}
              placeholder="Habesha Coffee PLC"
            />
          </Field>
          <Field label="Phone (optional, shown to customer)">
            <input
              className={inputClass}
              value={form.phone ?? ""}
              onChange={(e) => update("phone", e.target.value)}
              placeholder="+251911111111"
            />
          </Field>
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium px-4 py-2 transition disabled:opacity-60"
            >
              {createMutation.isPending ? "Saving…" : "Save account"}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowForm(false);
                setForm(EMPTY_FORM);
              }}
              className="rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 font-medium px-4 py-2"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <ul className="space-y-3">
        {accounts.map((a) => (
          <AccountRow
            key={a.id}
            account={a}
            canEdit={canEdit}
            onToggle={(isActive) => toggleMutation.mutate({ id: a.id, isActive })}
            onDelete={() => {
              if (confirm(`Delete account "${a.account_holder_name}"?`)) {
                deleteMutation.mutate(a.id);
              }
            }}
          />
        ))}
      </ul>
    </div>
  );
}

const inputClass =
  "w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500";

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1">
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      {children}
    </div>
  );
}

function AccountRow({
  account,
  canEdit,
  onToggle,
  onDelete,
}: {
  account: PaymentAccount;
  canEdit: boolean;
  onToggle: (isActive: boolean) => void;
  onDelete: () => void;
}) {
  return (
    <li className="bg-white border border-slate-200 rounded-2xl p-4 flex items-start justify-between gap-3">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2 mb-1">
          <span className="font-semibold text-slate-900">{account.bank_name}</span>
          {account.is_active ? (
            <span className="text-[10px] font-semibold uppercase bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded">
              Active
            </span>
          ) : (
            <span className="text-[10px] font-semibold uppercase bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
              Inactive
            </span>
          )}
        </div>
        <p className="text-sm text-slate-700 font-mono">{account.account_number}</p>
        <p className="text-sm text-slate-600">{account.account_holder_name}</p>
        {account.phone && <p className="text-sm text-slate-500">{account.phone}</p>}
      </div>
      {canEdit && (
        <div className="flex flex-col gap-2 shrink-0">
          <button
            onClick={() => onToggle(!account.is_active)}
            className="text-xs font-medium text-slate-700 hover:text-slate-900 px-3 py-1 rounded border border-slate-200 hover:bg-slate-50"
          >
            {account.is_active ? "Deactivate" : "Activate"}
          </button>
          <button
            onClick={onDelete}
            className="text-xs font-medium text-red-700 hover:text-red-900 px-3 py-1 rounded border border-red-200 hover:bg-red-50"
          >
            Delete
          </button>
        </div>
      )}
    </li>
  );
}
