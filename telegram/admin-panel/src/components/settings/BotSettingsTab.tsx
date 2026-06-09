import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getTelegramConfig,
  upsertTelegramConfig,
  deleteTelegramConfig,
  type LanguagePref,
} from "../../lib/telegramConfigApi";
import { useHasRole } from "../RoleGate";

export function BotSettingsTab() {
  const canEdit = useHasRole(["ADMIN"]);
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["telegramConfig"],
    queryFn: getTelegramConfig,
  });

  const [botToken, setBotToken] = useState("");
  const [language, setLanguage] = useState<LanguagePref>("AUTO");
  const [welcome, setWelcome] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (data) {
      setLanguage(data.language_preference);
      setWelcome(data.welcome_message ?? "");
    }
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: () =>
      upsertTelegramConfig({
        bot_token: botToken,
        language_preference: language,
        welcome_message: welcome || null,
      }),
    onSuccess: () => {
      setBotToken("");
      setError(null);
      qc.invalidateQueries({ queryKey: ["telegramConfig"] });
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      setError(humanize(typeof detail === "string" ? detail : "save_failed"));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteTelegramConfig,
    onSuccess: () => {
      setBotToken("");
      qc.invalidateQueries({ queryKey: ["telegramConfig"] });
    },
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!botToken) {
      setError("Please paste a bot token.");
      return;
    }
    saveMutation.mutate();
  }

  if (isLoading) return <p className="text-slate-500">Loading…</p>;

  return (
    <div className="space-y-6">
      {/* Current status */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-2">
          <h3 className="font-semibold text-slate-900">Current status</h3>
          {data?.is_active ? (
            <span className="text-xs font-semibold uppercase bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded">
              Active
            </span>
          ) : (
            <span className="text-xs font-semibold uppercase bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
              Not configured
            </span>
          )}
        </div>
        {data?.bot_username ? (
          <p className="text-sm text-slate-700">
            Connected as <span className="font-mono">@{data.bot_username}</span>
          </p>
        ) : (
          <p className="text-sm text-slate-500">
            No bot connected yet. Get a bot token from{" "}
            <a
              href="https://t.me/BotFather"
              target="_blank"
              rel="noreferrer"
              className="text-brand-600 hover:text-brand-700 font-medium"
            >
              @BotFather
            </a>{" "}
            and paste it below.
          </p>
        )}
      </div>

      {!canEdit && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm px-3 py-2">
          You're in read-only mode. Only ADMIN can change bot settings.
        </div>
      )}

      <form
        onSubmit={onSubmit}
        className={`bg-white border border-slate-200 rounded-2xl p-5 space-y-4 ${
          !canEdit ? "opacity-60 pointer-events-none" : ""
        }`}
      >
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Bot token {data ? "(paste again to update)" : "*"}
          </label>
          <input
            type="password"
            autoComplete="off"
            value={botToken}
            onChange={(e) => setBotToken(e.target.value)}
            className="w-full font-mono text-sm rounded-lg border border-slate-300 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
            placeholder="123456789:ABC-DEF..."
          />
          <p className="text-xs text-slate-500 mt-1">
            Stored encrypted with Fernet. We call Telegram's <code>getMe</code> to verify.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Default reply language
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as LanguagePref)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2.5 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="AUTO">Auto-detect from customer message</option>
            <option value="AMHARIC">አማርኛ (Amharic)</option>
            <option value="ENGLISH">English</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Welcome message (sent on /start)
          </label>
          <textarea
            rows={4}
            value={welcome}
            onChange={(e) => setWelcome(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
            placeholder="Welcome to Habesha Coffee! 🌟 Tap a product below to start shopping."
          />
          <p className="text-xs text-slate-500 mt-1">
            Leave blank to use a friendly default.
          </p>
        </div>

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saveMutation.isPending}
            className="rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium px-4 py-2.5 transition disabled:opacity-60"
          >
            {saveMutation.isPending ? "Saving…" : data ? "Update bot" : "Connect bot"}
          </button>
          {data && (
            <button
              type="button"
              onClick={() => {
                if (confirm("Disconnect this bot? Your customers will no longer receive replies.")) {
                  deleteMutation.mutate();
                }
              }}
              disabled={deleteMutation.isPending}
              className="rounded-lg border border-red-200 text-red-700 hover:bg-red-50 font-medium px-4 py-2.5 transition disabled:opacity-60"
            >
              {deleteMutation.isPending ? "Removing…" : "Disconnect bot"}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}

function humanize(code: string): string {
  switch (code) {
    case "invalid_token":
      return "Telegram rejected that token. Double-check it from @BotFather.";
    case "telegram_unreachable":
      return "Couldn't reach Telegram from the server. Try again in a moment.";
    case "no_merchant_context":
      return "Your account isn't linked to a merchant.";
    default:
      return code.replaceAll("_", " ");
  }
}
