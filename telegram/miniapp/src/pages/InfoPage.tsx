import { useQuery } from "@tanstack/react-query";
import {
  HiOutlineBuildingLibrary,
  HiOutlineChatBubbleLeftEllipsis,
  HiOutlinePhone,
  HiOutlineEnvelope,
  HiOutlineMapPin,
  HiOutlineSparkles,
  HiOutlineClipboardDocument,
} from "react-icons/hi2";
import { getMerchantInfo } from "../lib/catalogApi";
import { hapticImpact } from "../lib/telegram";

type IconCmp = React.ComponentType<{ className?: string }>;

const KIND_META: Record<string, { label: string; Icon: IconCmp }> = {
  TELEGRAM_USERNAME: { label: "Telegram", Icon: HiOutlineChatBubbleLeftEllipsis },
  PHONE: { label: "Phone", Icon: HiOutlinePhone },
  EMAIL: { label: "Email", Icon: HiOutlineEnvelope },
  ADDRESS: { label: "Address", Icon: HiOutlineMapPin },
  OTHER: { label: "Other", Icon: HiOutlineSparkles },
};

export default function InfoPage() {
  const { data: info, isLoading } = useQuery({
    queryKey: ["merchantInfo"],
    queryFn: getMerchantInfo,
  });

  if (isLoading) return <p className="p-6 text-tg-hint">Loading…</p>;
  if (!info) return null;

  const grouped = info.dm_contacts.reduce<Record<string, typeof info.dm_contacts>>(
    (acc, c) => {
      (acc[c.kind] ||= []).push(c);
      return acc;
    },
    {}
  );

  return (
    <div className="p-4 pb-24 animate-fade-in">
      {/* Hero card */}
      <div className="rounded-3xl bg-gradient-to-br from-brand-500 via-brand-600 to-brand-700 text-white p-5 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-white/15 grid place-items-center backdrop-blur">
            <HiOutlineSparkles className="w-6 h-6" />
          </div>
          <div className="min-w-0">
            <h1 className="text-lg font-bold leading-tight">{info.business_name}</h1>
            {info.business_description && (
              <p className="text-xs opacity-90 mt-0.5 line-clamp-2">{info.business_description}</p>
            )}
          </div>
        </div>
      </div>

      {info.payment_accounts.length > 0 && (
        <section className="mt-5">
          <h2 className="text-xs font-bold uppercase tracking-wider text-tg-hint mb-2 px-1 flex items-center gap-1.5">
            <HiOutlineBuildingLibrary className="w-3.5 h-3.5" /> Pay to
          </h2>
          <ul className="space-y-2">
            {info.payment_accounts.map((a, i) => (
              <li key={i} className="card card-pad animate-slide-up">
                <p className="text-sm font-bold text-tg-text">{a.bank_name}</p>
                <button
                  onClick={() => {
                    navigator.clipboard?.writeText(a.account_number);
                    hapticImpact("light");
                  }}
                  className="mt-1.5 inline-flex items-center gap-2 bg-tg-secondaryBg rounded-xl px-3 py-1.5 hover:bg-slate-200 active:scale-95 transition"
                >
                  <span className="text-sm font-mono font-bold text-brand-700">{a.account_number}</span>
                  <HiOutlineClipboardDocument className="w-3.5 h-3.5 text-tg-hint" />
                </button>
                <p className="text-xs text-tg-hint mt-1.5">{a.account_holder_name}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {Object.keys(grouped).length > 0 && (
        <section className="mt-6">
          <h2 className="text-xs font-bold uppercase tracking-wider text-tg-hint mb-2 px-1 flex items-center gap-1.5">
            <HiOutlineChatBubbleLeftEllipsis className="w-3.5 h-3.5" /> Contact us
          </h2>
          {Object.entries(grouped).map(([kind, items]) => {
            const meta = KIND_META[kind] ?? KIND_META.OTHER;
            const Icon = meta.Icon;
            return (
              <div key={kind} className="mt-3">
                <p className="text-[10px] text-tg-hint uppercase tracking-wide font-semibold px-1">
                  {meta.label}
                </p>
                <ul className="space-y-2 mt-1.5">
                  {items
                    .sort((a, b) => a.position - b.position)
                    .map((c, i) => (
                      <li key={i} className="card card-pad flex items-center gap-3 animate-slide-up">
                        <div className="w-9 h-9 rounded-xl bg-brand-50 text-brand-600 grid place-items-center shrink-0">
                          <Icon className="w-4.5 h-4.5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <ContactRow kind={kind} value={c.value} label={c.label} />
                        </div>
                      </li>
                    ))}
                </ul>
              </div>
            );
          })}
        </section>
      )}
    </div>
  );
}

function ContactRow({
  kind,
  value,
  label,
}: {
  kind: string;
  value: string;
  label: string | null;
}) {
  const inner = (
    <>
      <span className="font-semibold text-tg-text text-sm">{value}</span>
      {label && <span className="text-tg-hint text-xs block mt-0.5">{label}</span>}
    </>
  );
  if (kind === "TELEGRAM_USERNAME") {
    return (
      <a
        href={`https://t.me/${value.replace(/^@/, "")}`}
        target="_blank"
        rel="noreferrer"
        className="block"
      >
        {inner}
      </a>
    );
  }
  if (kind === "PHONE") {
    return (
      <a href={`tel:${value}`} className="block">
        {inner}
      </a>
    );
  }
  if (kind === "EMAIL") {
    return (
      <a href={`mailto:${value}`} className="block">
        {inner}
      </a>
    );
  }
  return <div>{inner}</div>;
}
