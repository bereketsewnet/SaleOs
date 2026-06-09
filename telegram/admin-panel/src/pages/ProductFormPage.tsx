import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createProduct,
  getProduct,
  runOcr,
  updateProduct,
  deleteProduct,
} from "../lib/productsApi";
import { getChannelStatus } from "../lib/telegramChannelApi";
import { getTelegramAISettings } from "../lib/telegramAiApi";
import { getTelegramConfig } from "../lib/telegramConfigApi";
import { ImageUploader } from "../components/ImageUploader";

const EMPTY = {
  title: "",
  description: "",
  base_price: "",
  sku: "",
  initial_stock: 0,
  identifier: "",
  instructions: "",
};

export default function ProductFormPage() {
  const { productId } = useParams<{ productId: string }>();
  const isEdit = !!productId;
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: existing, isLoading: loadingExisting } = useQuery({
    queryKey: ["product", productId],
    queryFn: () => getProduct(productId!),
    enabled: isEdit,
  });
  const { data: channelStatus } = useQuery({
    queryKey: ["channelStatus"],
    queryFn: getChannelStatus,
  });
  const { data: aiSettings } = useQuery({
    queryKey: ["telegramAI"],
    queryFn: getTelegramAISettings,
  });
  const { data: telegramConfig } = useQuery({
    queryKey: ["telegramConfig"],
    queryFn: getTelegramConfig,
  });

  const [form, setForm] = useState(EMPTY);
  const [imageUrls, setImageUrls] = useState<string[]>([]);
  const [publishToChannel, setPublishToChannel] = useState(true);
  const [advanceOpen, setAdvanceOpen] = useState(false);
  const [runOcrOnSave, setRunOcrOnSave] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Poll product after dispatching OCR so the identifier appears once Telegram svc PATCHes back.
  const aiKeySet = aiSettings?.ai_api_key_set === true;
  const aiProvider = aiSettings?.ai_provider ?? null;
  const ocrAvailable = !!aiProvider && aiKeySet;

  useEffect(() => {
    if (existing) {
      setForm({
        title: existing.title,
        description: existing.description ?? "",
        base_price: existing.base_price ?? "",
        sku: existing.sku ?? "",
        initial_stock: existing.quantity,
        identifier: existing.identifier ?? "",
        instructions: existing.instructions ?? "",
      });
      setImageUrls(existing.image_urls);
      if (existing.identifier || existing.instructions || existing.is_ocr_identified) {
        setAdvanceOpen(true);
      }
    }
  }, [existing]);

  // NEW product: prefill identifier + instructions from the merchant's defaults
  // so the merchant doesn't have to retype boilerplate. They can edit or clear.
  useEffect(() => {
    if (isEdit || !telegramConfig) return;
    const defId = telegramConfig.default_product_identifier ?? "";
    const defIns = telegramConfig.default_product_instructions ?? "";
    if (!defId && !defIns) return;
    setForm((prev) => ({
      ...prev,
      identifier: prev.identifier || defId,
      instructions: prev.instructions || defIns,
    }));
    setAdvanceOpen(true);
  }, [isEdit, telegramConfig]);

  const createMutation = useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["products"] });
      qc.invalidateQueries({ queryKey: ["channelPosts"] });
      navigate("/products");
    },
    onError: (err: any) => setError(humanize(err?.response?.data?.detail)),
  });

  const updateMutation = useMutation({
    mutationFn: (data: any) => updateProduct(productId!, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["products"] });
      qc.invalidateQueries({ queryKey: ["product", productId] });
      navigate("/products");
    },
    onError: (err: any) => setError(humanize(err?.response?.data?.detail)),
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteProduct(productId!),
    onSuccess: (summary) => {
      qc.invalidateQueries({ queryKey: ["products"] });
      qc.invalidateQueries({ queryKey: ["channelPosts"] });
      if (summary.channel_messages_failed > 0 && summary.channel_reason !== "already_gone") {
        if (summary.channel_reason === "missing_delete_permission") {
          alert(
            `Product deleted, but the bot doesn't have "Delete messages" permission in your channel — ` +
              `${summary.channel_messages_failed} message(s) remain on the channel. ` +
              `Delete them manually in Telegram, then grant the permission in Settings → Channel.`
          );
        } else {
          alert(
            `Product deleted, but ${summary.channel_messages_failed} channel message(s) could not be removed.`
          );
        }
      }
      navigate("/products");
    },
  });

  function update<K extends keyof typeof form>(k: K, v: string | number) {
    setForm((prev) => ({ ...prev, [k]: v }));
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const sku = form.sku.trim() || null;
    const base_price = form.base_price.trim() || null;
    const identifier = form.identifier.trim() || null;
    const instructions = form.instructions.trim() || null;
    if (isEdit) {
      updateMutation.mutate({
        title: form.title,
        description: form.description || null,
        base_price: base_price ?? undefined,
        sku: sku ?? undefined,
        image_urls: imageUrls,
        identifier,
        instructions,
      });
      // After updating an edit, fire off OCR if user toggled it on this session.
      if (runOcrOnSave && imageUrls.length > 0 && productId) {
        runOcr(productId).catch(() => null);
      }
    } else {
      createMutation.mutate({
        title: form.title,
        description: form.description || null,
        base_price,
        sku,
        image_urls: imageUrls,
        initial_stock: form.initial_stock || 0,
        publish_to_channel: publishToChannel && !!channelStatus?.connected,
        identifier,
        instructions,
        run_ocr: runOcrOnSave && imageUrls.length > 0,
      });
    }
  }

  // Warning fires when nothing is set and OCR hasn't filled anything either.
  const contextWarning =
    !form.identifier.trim() &&
    !form.instructions.trim() &&
    !existing?.is_ocr_identified;

  if (isEdit && loadingExisting) return <p className="text-slate-500">Loading…</p>;

  const submitting = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="max-w-3xl">
      <div className="mb-4">
        <Link to="/products" className="text-sm text-slate-600 hover:text-slate-900">
          ← Back to products
        </Link>
      </div>
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <h1 className="text-2xl sm:text-3xl font-semibold text-slate-900">
          {isEdit ? "Edit product" : "New product"}
        </h1>
        {isEdit && existing && (existing.is_published_to_channel ? (
          <span className="text-xs font-semibold uppercase bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded">
            ✓ Published
          </span>
        ) : (
          <span className="text-xs font-semibold uppercase bg-amber-100 text-amber-800 px-2 py-0.5 rounded">
            Not published
          </span>
        ))}
      </div>
      {isEdit && (
        <p className="text-sm text-slate-500 mb-6">
          Saving any change resets the channel state — click <span className="font-medium">Publish to channel</span> on the Products page to repost the updated version.
        </p>
      )}
      {!isEdit && <div className="mb-6" />}

      <form onSubmit={onSubmit} className="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 space-y-5">
        <Field label="Title" required>
          <input
            required
            className={inputClass}
            value={form.title}
            onChange={(e) => update("title", e.target.value)}
            placeholder="Single-origin Sidamo · 250g"
          />
        </Field>

        <Field label="Description">
          <textarea
            rows={3}
            className={inputClass}
            value={form.description}
            onChange={(e) => update("description", e.target.value)}
            placeholder="Notes, origin, certifications…"
          />
        </Field>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Field label="Price (ETB)">
            <input
              type="number"
              min="0"
              step="0.01"
              className={inputClass}
              value={form.base_price}
              onChange={(e) => update("base_price", e.target.value)}
              placeholder="optional"
            />
          </Field>
          <Field label="SKU">
            <input
              className={inputClass}
              value={form.sku}
              onChange={(e) => update("sku", e.target.value)}
              placeholder="optional — auto-generated"
            />
          </Field>
          {!isEdit && (
            <Field label="Initial stock">
              <input
                type="number"
                min="0"
                className={inputClass}
                value={form.initial_stock}
                onChange={(e) => update("initial_stock", parseInt(e.target.value || "0", 10))}
              />
            </Field>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">Images</label>
          <ImageUploader urls={imageUrls} onChange={setImageUrls} />
        </div>

        {/* Advance toggle: identifier + instructions + OCR */}
        <div className="border-t border-slate-200 pt-4">
          <button
            type="button"
            onClick={() => setAdvanceOpen((v) => !v)}
            className="text-sm font-medium text-slate-700 hover:text-slate-900 flex items-center gap-1.5"
          >
            <span className={`transition-transform ${advanceOpen ? "rotate-90" : ""}`}>
              ▶
            </span>
            Advance · AI agent context
            {existing?.is_ocr_identified && (
              <span className="ml-2 text-[10px] font-semibold uppercase bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded">
                Identified by OCR
              </span>
            )}
          </button>

          {advanceOpen && (
            <div className="mt-4 space-y-4">
              {contextWarning && (
                <div className="rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm px-3 py-2">
                  ⚠ Product identifier or instructions not set — the AI agent
                  will fall back to your defaults from{" "}
                  <Link to="/settings" className="font-medium underline">
                    Settings → Brand Voice
                  </Link>
                  .
                </div>
              )}

              <Field label="Identifier (private — not shown publicly)">
                <textarea
                  rows={3}
                  className={inputClass}
                  value={form.identifier}
                  onChange={(e) => update("identifier", e.target.value)}
                  placeholder={
                    "What is this product? E.g. Red Nike Air shoes size 42, 4 in stock, also have black + white"
                  }
                />
                <p className="text-xs text-slate-500 mt-1">
                  Private to the AI agent. Use any language — Amharic, English, mixed.
                </p>
              </Field>

              <Field label="Instructions for the agent about this product">
                <textarea
                  rows={3}
                  className={inputClass}
                  value={form.instructions}
                  onChange={(e) => update("instructions", e.target.value)}
                  placeholder={
                    "How should the bot reply about THIS product? E.g. Don't tell the price publicly — send my first Telegram username and first phone instead."
                  }
                />
              </Field>

              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
                <label
                  className={`flex items-start gap-3 cursor-pointer ${
                    !ocrAvailable || imageUrls.length === 0 ? "opacity-60" : ""
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={runOcrOnSave}
                    onChange={(e) => setRunOcrOnSave(e.target.checked)}
                    disabled={!ocrAvailable || imageUrls.length === 0}
                    className="mt-1"
                  />
                  <div>
                    <p className="font-medium text-slate-900">Identify by OCR (vision)</p>
                    <p className="text-sm text-slate-600">
                      {!ocrAvailable ? (
                        <>
                          Configure an AI provider + key in{" "}
                          <Link to="/settings" className="underline">
                            Settings → AI Agents
                          </Link>{" "}
                          first.
                        </>
                      ) : imageUrls.length === 0 ? (
                        "Add at least one image."
                      ) : (
                        <>
                          On save, the bot will run vision on the images and fill the
                          identifier above. Powered by your configured{" "}
                          <span className="font-mono">{aiProvider}</span> model.
                        </>
                      )}
                    </p>
                  </div>
                </label>
              </div>
            </div>
          )}
        </div>

        {!isEdit && (
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={publishToChannel}
                onChange={(e) => setPublishToChannel(e.target.checked)}
                disabled={!channelStatus?.connected}
                className="mt-1"
              />
              <div>
                <p className="font-medium text-slate-900">
                  Publish to my Telegram channel right after saving
                </p>
                <p className="text-sm text-slate-600">
                  {channelStatus?.connected ? (
                    <>
                      The bot will post the title, description, price and first image to{" "}
                      <span className="font-mono">
                        {channelStatus.channel_username
                          ? `@${channelStatus.channel_username}`
                          : channelStatus.channel_title}
                      </span>
                      .
                    </>
                  ) : (
                    <>
                      Connect your channel first (Settings → Channel) to enable this.
                    </>
                  )}
                </p>
              </div>
            </label>
          </div>
        )}

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
            {error}
          </div>
        )}

        <div className="flex flex-wrap gap-3">
          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium px-4 py-2.5 disabled:opacity-60"
          >
            {submitting ? "Saving…" : isEdit ? "Save changes" : "Create product"}
          </button>
          <Link
            to="/products"
            className="rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 font-medium px-4 py-2.5"
          >
            Cancel
          </Link>
          {isEdit && (
            <button
              type="button"
              onClick={() => {
                if (confirm("Delete this product? This can't be undone.")) {
                  deleteMutation.mutate();
                }
              }}
              disabled={deleteMutation.isPending}
              className="ml-auto rounded-lg border border-red-200 text-red-700 hover:bg-red-50 font-medium px-4 py-2.5"
            >
              {deleteMutation.isPending ? "Deleting…" : "Delete"}
            </button>
          )}
        </div>
      </form>
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

function humanize(code: string | undefined): string {
  switch (code) {
    case "sku_already_used":
      return "That SKU is already used by another product.";
    case "no_merchant_context":
      return "Your account isn't linked to a merchant.";
    default:
      return code ? code.replaceAll("_", " ") : "Something went wrong.";
  }
}
