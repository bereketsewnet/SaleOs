import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  DEFAULT_MODELS,
  PROVIDER_LABELS,
  getTelegramAISettings,
  updateTelegramAISettings,
  type AIProvider,
} from "../../lib/telegramAiApi";
import { useHasRole } from "../RoleGate";

export function AIAgentsTab() {
  const canEdit = useHasRole(["ADMIN"]);
  const qc = useQueryClient();

  const { data: settings, isLoading } = useQuery({
    queryKey: ["telegramAI"],
    queryFn: getTelegramAISettings,
  });

  const [provider, setProvider] = useState<AIProvider | "">("");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");
  const [replyDm, setReplyDm] = useState(false);
  const [replyComments, setReplyComments] = useState(false);
  const [parseHashtag, setParseHashtag] = useState(true);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (settings) {
      setProvider(settings.ai_provider ?? "");
      setModel(settings.ai_model ?? "");
      setReplyDm(settings.ai_auto_reply_dm);
      setReplyComments(settings.ai_auto_reply_comments);
      setParseHashtag(settings.ai_parse_hashtag_products);
    }
  }, [settings]);

  const saveMutation = useMutation({
    mutationFn: () =>
      updateTelegramAISettings({
        ai_provider: provider || null,
        // Send the key only if the user typed something. Empty means no change.
        ai_api_key: apiKey ? apiKey : undefined,
        ai_model: model || null,
        ai_auto_reply_dm: replyDm,
        ai_auto_reply_comments: replyComments,
        ai_parse_hashtag_products: parseHashtag,
      }),
    onSuccess: () => {
      setApiKey("");
      setError(null);
      setSaved(true);
      setTimeout(() => setSaved(false), 2200);
      qc.invalidateQueries({ queryKey: ["telegramAI"] });
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      setError(humanize(typeof detail === "string" ? detail : "save_failed"));
    },
  });

  function applyProviderDefault(p: AIProvider | "") {
    setProvider(p);
    if (p && !model) setModel(DEFAULT_MODELS[p]);
  }

  function clearKey() {
    if (!confirm("Clear the saved API key?")) return;
    updateTelegramAISettings({ ai_api_key: "" }).then(() =>
      qc.invalidateQueries({ queryKey: ["telegramAI"] })
    );
  }

  if (isLoading) return <p className="text-slate-500">Loading…</p>;

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
        <span className="font-semibold text-slate-900">Telegram-only.</span> AI
        provider and toggles below power: <span className="font-medium">customer
        DM auto-replies</span>, <span className="font-medium">channel comment
        auto-replies</span>, and <span className="font-medium">manual <code className="text-[12px] bg-white border border-slate-200 rounded px-1">#product</code> post</span> auto-import.
      </div>

      {!settings && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm px-3 py-2">
          Connect your bot first (Telegram Bot tab) before configuring AI.
        </div>
      )}

      {!canEdit && settings && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm px-3 py-2">
          Read-only mode. Only ADMIN can change AI settings.
        </div>
      )}

      <form
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
          saveMutation.mutate();
        }}
        className={`bg-white border border-slate-200 rounded-2xl p-5 space-y-5 ${
          !canEdit || !settings ? "opacity-60 pointer-events-none" : ""
        }`}
      >
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Provider
          </label>
          <select
            value={provider}
            onChange={(e) => applyProviderDefault(e.target.value as AIProvider | "")}
            className={inputClass}
          >
            <option value="">— Select a provider —</option>
            <option value="GEMINI">{PROVIDER_LABELS.GEMINI}</option>
            <option value="OPENAI">{PROVIDER_LABELS.OPENAI}</option>
            <option value="CLAUDE">{PROVIDER_LABELS.CLAUDE}</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            API key
            {settings?.ai_api_key_set && (
              <span className="ml-2 text-xs font-semibold uppercase bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded">
                ✓ Saved
              </span>
            )}
          </label>
          <input
            type="password"
            autoComplete="off"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className={`${inputClass} font-mono text-sm`}
            placeholder={
              settings?.ai_api_key_set
                ? "Paste a new key to replace, or leave blank"
                : "Paste your API key"
            }
          />
          <p className="text-xs text-slate-500 mt-1">
            Stored encrypted with Fernet (AES-128) — never shown back.
          </p>
          {settings?.ai_api_key_set && canEdit && (
            <button
              type="button"
              onClick={clearKey}
              className="mt-2 text-xs font-medium border border-red-200 text-red-700 hover:bg-red-50 rounded-lg px-3 py-1"
            >
              Clear saved key
            </button>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Model
          </label>
          <input
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className={`${inputClass} font-mono text-sm`}
            placeholder={
              provider
                ? `default: ${DEFAULT_MODELS[provider as AIProvider]}`
                : "pick a provider first"
            }
          />
          <p className="text-xs text-slate-500 mt-1">
            Leave blank to use the provider's default. Smaller models = faster
            replies, lower cost.
          </p>
        </div>

        <div className="border-t border-slate-200 pt-4">
          <p className="text-sm font-medium text-slate-700 mb-2">
            Agent toggles
          </p>
          <div className="space-y-2">
            <Toggle
              checked={replyDm}
              onChange={setReplyDm}
              label="Auto-reply to DMs"
              hint="When a customer messages the bot directly, the AI answers in your brand voice."
            />
            <Toggle
              checked={replyComments}
              onChange={setReplyComments}
              label="Auto-reply to channel comments"
              hint="When someone comments under a channel post, the bot replies in the linked discussion group."
            />
            <Toggle
              checked={parseHashtag}
              onChange={setParseHashtag}
              label={
                <>
                  Auto-import manual posts tagged{" "}
                  <code className="text-[12px] bg-slate-100 border border-slate-200 rounded px-1">#product</code>
                </>
              }
              hint="When you post in the channel with #product in the caption, the bot parses title/price and creates a product with the images."
            />
          </div>
        </div>

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
            {error}
          </div>
        )}

        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={saveMutation.isPending}
            className="rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium px-4 py-2.5 disabled:opacity-60"
          >
            {saveMutation.isPending ? "Saving…" : "Save AI settings"}
          </button>
          {saved && <span className="text-sm text-emerald-700 font-medium">Saved ✓</span>}
        </div>
      </form>
    </div>
  );
}

const inputClass =
  "w-full rounded-lg border border-slate-300 px-3 py-2.5 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500";

function Toggle({
  checked,
  onChange,
  label,
  hint,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: React.ReactNode;
  hint: string;
}) {
  return (
    <label className="flex items-start gap-3 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-1"
      />
      <div>
        <p className="font-medium text-slate-900">{label}</p>
        <p className="text-sm text-slate-600">{hint}</p>
      </div>
    </label>
  );
}

function humanize(code: string): string {
  switch (code) {
    case "connect_bot_first":
      return "Connect your Telegram bot first.";
    case "no_merchant_context":
      return "Your account isn't linked to a merchant.";
    default:
      return code.replaceAll("_", " ");
  }
}
