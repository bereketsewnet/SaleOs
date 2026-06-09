import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getTelegramConfig,
  getTelegramPresets,
  updateTelegramBrandVoice,
} from "../../lib/telegramConfigApi";
import {
  getMerchantProfile,
  updateMerchantProfile,
} from "../../lib/merchantProfileApi";
import { useHasRole } from "../RoleGate";

export function BrandVoiceTab() {
  const canEdit = useHasRole(["ADMIN"]);
  const qc = useQueryClient();

  const { data: config, isLoading } = useQuery({
    queryKey: ["telegramConfig"],
    queryFn: getTelegramConfig,
  });
  const { data: presets } = useQuery({
    queryKey: ["telegramPresets"],
    queryFn: getTelegramPresets,
  });
  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ["merchantProfile"],
    queryFn: getMerchantProfile,
  });

  const [businessName, setBusinessName] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [businessType, setBusinessType] = useState("");
  const [description, setDescription] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [defaultIdentifier, setDefaultIdentifier] = useState("");
  const [defaultInstructions, setDefaultInstructions] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (config) {
      setBusinessType(config.business_type ?? "");
      setDescription(config.business_description ?? "");
      setSystemPrompt(config.system_prompt ?? "");
      setDefaultIdentifier(config.default_product_identifier ?? "");
      setDefaultInstructions(config.default_product_instructions ?? "");
    }
  }, [config]);

  useEffect(() => {
    if (profile) {
      setBusinessName(profile.business_name);
      setContactPhone(profile.contact_phone);
      setContactEmail(profile.contact_email);
    }
  }, [profile]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      const needsIdentityUpdate =
        profile &&
        (businessName.trim() !== profile.business_name ||
          contactPhone.trim() !== profile.contact_phone ||
          contactEmail.trim() !== profile.contact_email);
      if (needsIdentityUpdate) {
        await updateMerchantProfile({
          business_name: businessName.trim(),
          contact_phone: contactPhone.trim(),
          contact_email: contactEmail.trim(),
        });
      }
      return updateTelegramBrandVoice({
        business_type: businessType || null,
        business_description: description || null,
        system_prompt: systemPrompt || null,
        default_product_identifier: defaultIdentifier || null,
        default_product_instructions: defaultInstructions || null,
      });
    },
    onSuccess: () => {
      setError(null);
      setSaved(true);
      setTimeout(() => setSaved(false), 2200);
      qc.invalidateQueries({ queryKey: ["telegramConfig"] });
      qc.invalidateQueries({ queryKey: ["merchantProfile"] });
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail;
      setError(humanize(typeof detail === "string" ? detail : "save_failed"));
    },
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    saveMutation.mutate();
  }

  function applyTemplate(template: string) {
    setSystemPrompt(template);
  }

  if (isLoading || profileLoading) return <p className="text-slate-500">Loading…</p>;

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
        <span className="font-semibold text-slate-900">Telegram-only.</span> These
        settings shape how <span className="font-medium">your Telegram bot</span>
        {" "}sounds. TikTok, Instagram and Facebook each get their own brand voice
        on their own admin panel.
      </div>

      {!config && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm px-3 py-2">
          Connect your bot first (Telegram Bot tab) before setting the brand voice.
        </div>
      )}

      {!canEdit && config && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm px-3 py-2">
          Read-only mode. Only ADMIN can change brand voice.
        </div>
      )}

      <form
        onSubmit={onSubmit}
        className={`bg-white border border-slate-200 rounded-2xl p-5 space-y-5 ${
          !canEdit || !config ? "opacity-60 pointer-events-none" : ""
        }`}
      >
        {/* Business identity — applies everywhere (admin panel, Mini App, bot replies) */}
        <div className="pb-4 border-b border-slate-200">
          <h3 className="text-sm font-semibold text-slate-900 mb-1">Business identity</h3>
          <p className="text-xs text-slate-500 mb-3">
            Shown to customers in the Mini App, the bot's greeting, and the AI agent's replies.
            Saving here also reloads the bot so it speaks the new name immediately.
          </p>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Business name <span className="text-red-500">*</span>
              </label>
              <input
                required
                minLength={2}
                maxLength={255}
                className={inputClass}
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                placeholder="Habesha Coffee"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Contact phone
                </label>
                <input
                  type="tel"
                  className={inputClass}
                  value={contactPhone}
                  onChange={(e) => setContactPhone(e.target.value)}
                  placeholder="+251911111111"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Contact email
                </label>
                <input
                  type="email"
                  className={inputClass}
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                  placeholder="contact@habesha.com"
                />
              </div>
            </div>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            What kind of business are you?
          </label>
          <input
            list="bt-options"
            value={businessType}
            onChange={(e) => setBusinessType(e.target.value)}
            className={inputClass}
            placeholder="e.g. Coffee shop, Tax consultancy, Tutoring center…"
          />
          <datalist id="bt-options">
            {(presets?.business_types ?? []).map((t) => (
              <option key={t} value={t} />
            ))}
          </datalist>
          <p className="text-xs text-slate-500 mt-1">
            Helps your bot speak in your domain (products vs. appointments vs. classes…).
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            One-line business description
          </label>
          <textarea
            rows={2}
            maxLength={2000}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className={inputClass}
            placeholder="Single-origin Ethiopian coffee, roasted in Addis."
          />
          <p className="text-xs text-slate-500 mt-1">
            Shown to customers when the bot greets them on /start (if you haven't set a custom welcome message).
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            System prompt (AI persona &amp; rules)
          </label>
          <textarea
            rows={8}
            maxLength={8000}
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            className={`${inputClass} font-mono text-[13px]`}
            placeholder="You are the friendly assistant for…&#10;&#10;Tone: warm, concise.&#10;Always reply in the same language the customer used.&#10;If you don't know an answer, offer to connect a human."
          />
          <div className="flex flex-wrap gap-2 mt-2">
            <TemplateChip onClick={() => applyTemplate(RETAIL_TEMPLATE)}>
              Retail shop
            </TemplateChip>
            <TemplateChip onClick={() => applyTemplate(CONSULTANCY_TEMPLATE)}>
              Consultancy
            </TemplateChip>
            <TemplateChip onClick={() => applyTemplate(RESTAURANT_TEMPLATE)}>
              Restaurant
            </TemplateChip>
            <TemplateChip onClick={() => applyTemplate(SERVICE_TEMPLATE)}>
              Service provider
            </TemplateChip>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            This is the instruction the bot reads before every AI reply. Click a chip
            to start from a template, then edit.
          </p>
        </div>

        <div className="border-t border-slate-200 pt-4">
          <h3 className="text-sm font-semibold text-slate-900 mb-2">
            Default product context
          </h3>
          <p className="text-xs text-slate-500 mb-3">
            Auto-applied to <span className="font-medium">every product</span> that doesn't override these fields. Use Amharic, English or mixed.
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Default product identifier
              </label>
              <textarea
                rows={3}
                maxLength={4000}
                value={defaultIdentifier}
                onChange={(e) => setDefaultIdentifier(e.target.value)}
                className={inputClass}
                placeholder="E.g. We sell shoes in sizes 38–46. All in stock unless told otherwise. Colors: black / white / red."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Default reply instructions
              </label>
              <textarea
                rows={3}
                maxLength={4000}
                value={defaultInstructions}
                onChange={(e) => setDefaultInstructions(e.target.value)}
                className={inputClass}
                placeholder="E.g. Don't share prices in public comments — send the first phone number and ask the customer to DM."
              />
            </div>
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
            className="rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium px-4 py-2.5 transition disabled:opacity-60"
          >
            {saveMutation.isPending ? "Saving…" : "Save brand voice"}
          </button>
          {saved && (
            <span className="text-sm text-emerald-700 font-medium">Saved ✓</span>
          )}
        </div>
      </form>
    </div>
  );
}

const inputClass =
  "w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500";

function TemplateChip({
  onClick,
  children,
}: {
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="text-xs font-medium px-2.5 py-1 rounded-full border border-slate-300 text-slate-700 hover:bg-slate-50"
    >
      {children}
    </button>
  );
}

function humanize(code: string): string {
  switch (code) {
    case "connect_bot_first":
      return "Connect your Telegram bot in the Telegram Bot tab first.";
    case "no_merchant_context":
      return "Your account isn't linked to a merchant.";
    case "email_already_used":
      return "That email is already used by another merchant.";
    case "phone_already_used":
      return "That phone is already used by another merchant.";
    default:
      return code.replaceAll("_", " ");
  }
}

const RETAIL_TEMPLATE = `You are the Telegram assistant for a retail business.

Tone: warm, helpful, concise.
- Help customers find products, answer about pricing and availability.
- When a customer is ready to buy, send them the Mini App link to check out.
- Reply in the same language the customer used (Amharic or English).
- Never invent products or prices — only use what's in our catalog.`;

const CONSULTANCY_TEMPLATE = `You are the Telegram assistant for a consultancy.

Tone: professional, calm, clear.
- Answer questions about our services in 2-4 sentences.
- For pricing or scope, take the customer's contact info and let them know a consultant will follow up within one business day.
- Reply in the same language the customer used.
- Never promise specific outcomes or quote firm prices without human review.`;

const RESTAURANT_TEMPLATE = `You are the Telegram assistant for a restaurant.

Tone: friendly, appetizing, concise.
- Share menu items, today's specials, opening hours.
- For reservations or large orders, collect name + party size + time and confirm we'll follow up.
- Reply in the same language the customer used.
- Never confirm a reservation as final on your own.`;

const SERVICE_TEMPLATE = `You are the Telegram assistant for a service provider.

Tone: warm, professional, clear.
- Explain the services we offer in plain language.
- For booking requests, collect name, contact, and what they need help with.
- Reply in the same language the customer used.
- If a question is outside our services, say so honestly.`;
