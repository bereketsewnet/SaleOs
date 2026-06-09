import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createDMContact,
  deleteDMContact,
  KIND_LABELS,
  KIND_PLACEHOLDERS,
  listDMContacts,
  reorderDMContacts,
  updateDMContact,
  type DMContact,
  type DMContactKind,
} from "../../lib/telegramDmContactsApi";
import { useHasRole } from "../RoleGate";

const KIND_ORDER: DMContactKind[] = [
  "TELEGRAM_USERNAME",
  "PHONE",
  "EMAIL",
  "ADDRESS",
  "OTHER",
];

export function DmContactsTab() {
  const canEdit = useHasRole(["ADMIN"]);
  const qc = useQueryClient();
  const { data: contacts = [], isLoading } = useQuery({
    queryKey: ["dmContacts"],
    queryFn: listDMContacts,
  });

  const createMutation = useMutation({
    mutationFn: createDMContact,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dmContacts"] }),
  });
  const updateMutation = useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: any }) =>
      updateDMContact(id, patch),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dmContacts"] }),
  });
  const deleteMutation = useMutation({
    mutationFn: deleteDMContact,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dmContacts"] }),
  });
  const reorderMutation = useMutation({
    mutationFn: reorderDMContacts,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dmContacts"] }),
  });

  function move(contact: DMContact, direction: "up" | "down") {
    const siblings = contacts
      .filter((c) => c.kind === contact.kind)
      .sort((a, b) => a.position - b.position);
    const idx = siblings.findIndex((c) => c.id === contact.id);
    const target = direction === "up" ? idx - 1 : idx + 1;
    if (target < 0 || target >= siblings.length) return;
    const reordered = [...siblings];
    [reordered[idx], reordered[target]] = [reordered[target], reordered[idx]];
    reorderMutation.mutate(
      reordered.map((c, i) => ({ id: c.id, position: i }))
    );
  }

  if (isLoading) return <p className="text-slate-500">Loading…</p>;

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
        <span className="font-semibold text-slate-900">Telegram-only.</span> The
        AI agent reads these when an instruction says e.g. "send my first
        Telegram username and first phone". Drag with the arrows to reorder per
        kind — the <span className="font-medium">topmost active</span> entry is "the first".
      </div>

      {!canEdit && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm px-3 py-2">
          Read-only mode. Only ADMIN can change DM contacts.
        </div>
      )}

      {KIND_ORDER.map((kind) => {
        const rows = contacts
          .filter((c) => c.kind === kind)
          .sort((a, b) => a.position - b.position);
        return (
          <section key={kind} className="bg-white border border-slate-200 rounded-2xl p-5">
            <h3 className="font-semibold text-slate-900 mb-3">{KIND_LABELS[kind]}</h3>
            {rows.length === 0 ? (
              <p className="text-sm text-slate-500 mb-3">None yet.</p>
            ) : (
              <ul className="space-y-2 mb-3">
                {rows.map((c, idx) => (
                  <li
                    key={c.id}
                    className="flex flex-wrap items-center gap-2 border border-slate-200 rounded-xl p-3"
                  >
                    <div className="flex flex-col">
                      <button
                        type="button"
                        disabled={!canEdit || idx === 0}
                        onClick={() => move(c, "up")}
                        className="text-xs text-slate-600 hover:text-slate-900 disabled:opacity-30"
                      >
                        ▲
                      </button>
                      <button
                        type="button"
                        disabled={!canEdit || idx === rows.length - 1}
                        onClick={() => move(c, "down")}
                        className="text-xs text-slate-600 hover:text-slate-900 disabled:opacity-30"
                      >
                        ▼
                      </button>
                    </div>
                    <div className="font-mono text-sm flex-1 min-w-[180px]">{c.value}</div>
                    {c.label && (
                      <span className="text-xs text-slate-500">({c.label})</span>
                    )}
                    <label className="text-xs flex items-center gap-1">
                      <input
                        type="checkbox"
                        checked={c.is_active}
                        disabled={!canEdit}
                        onChange={(e) =>
                          updateMutation.mutate({
                            id: c.id,
                            patch: { is_active: e.target.checked },
                          })
                        }
                      />
                      Active
                    </label>
                    {canEdit && (
                      <button
                        type="button"
                        onClick={() => {
                          if (confirm(`Delete ${c.value}?`)) deleteMutation.mutate(c.id);
                        }}
                        className="text-xs border border-red-200 text-red-700 hover:bg-red-50 rounded-lg px-2 py-1"
                      >
                        Delete
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}
            {canEdit && (
              <AddRowForm
                kind={kind}
                nextPosition={rows.length}
                onAdd={(value, label) =>
                  createMutation.mutate({
                    kind,
                    value,
                    label: label || null,
                    position: rows.length,
                  })
                }
              />
            )}
          </section>
        );
      })}
    </div>
  );
}

function AddRowForm({
  kind,
  nextPosition,
  onAdd,
}: {
  kind: DMContactKind;
  nextPosition: number;
  onAdd: (value: string, label: string) => void;
}) {
  const [value, setValue] = useState("");
  const [label, setLabel] = useState("");
  function submit(e: FormEvent) {
    e.preventDefault();
    if (!value.trim()) return;
    onAdd(value.trim(), label.trim());
    setValue("");
    setLabel("");
  }
  return (
    <form onSubmit={submit} className="flex flex-wrap gap-2 items-center">
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="flex-1 min-w-[180px] rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        placeholder={KIND_PLACEHOLDERS[kind]}
      />
      <input
        value={label}
        onChange={(e) => setLabel(e.target.value)}
        className="w-32 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        placeholder="Label (optional)"
      />
      <button
        type="submit"
        className="rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-3 py-2"
      >
        + Add
      </button>
      <span className="text-xs text-slate-400">position {nextPosition}</span>
    </form>
  );
}
