import { useQuery } from "@tanstack/react-query";
import { getMerchantInfo } from "../lib/catalogApi";
import { hapticImpact } from "../lib/telegram";

const KIND_TITLES: Record<string, string> = {
  TELEGRAM_USERNAME: "Telegram",
  PHONE: "Phone",
  EMAIL: "Email",
  ADDRESS: "Address",
  OTHER: "Other",
};

export default function InfoPage() {
  const { data: info, isLoading } = useQuery({
    queryKey: ["merchantInfo"],
    queryFn: getMerchantInfo,
  });

  if (isLoading) return <p className="p-6 text-tg-hint">Loading…</p>;
  if (!info) return null;

  // Group contacts by kind
  const grouped = info.dm_contacts.reduce<Record<string, typeof info.dm_contacts>>(
    (acc, c) => {
      (acc[c.kind] ||= []).push(c);
      return acc;
    },
    {}
  );

  return (
    <div className="p-4 pb-24">
      <h1 className="text-lg font-semibold">{info.business_name}</h1>
      {info.business_description && (
        <p className="text-sm text-tg-hint mt-1">{info.business_description}</p>
      )}

      {info.payment_accounts.length > 0 && (
        <section className="mt-5">
          <h2 className="text-sm font-semibold mb-2">💳 Pay to</h2>
          <ul className="space-y-2">
            {info.payment_accounts.map((a, i) => (
              <li key={i} className="bg-tg-secondaryBg rounded-2xl p-3">
                <p className="text-sm font-medium">{a.bank_name}</p>
                <p
                  className="text-sm font-mono font-semibold mt-0.5"
                  onClick={() => {
                    navigator.clipboard?.writeText(a.account_number);
                    hapticImpact("light");
                  }}
                >
                  {a.account_number} 📋
                </p>
                <p className="text-xs text-tg-hint">{a.account_holder_name}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {Object.keys(grouped).length > 0 && (
        <section className="mt-5">
          <h2 className="text-sm font-semibold mb-2">📨 Contact us</h2>
          {Object.entries(grouped).map(([kind, items]) => (
            <div key={kind} className="mt-3">
              <p className="text-xs text-tg-hint uppercase tracking-wide">
                {KIND_TITLES[kind] ?? kind}
              </p>
              <ul className="space-y-2 mt-1">
                {items
                  .sort((a, b) => a.position - b.position)
                  .map((c, i) => (
                    <li key={i} className="bg-tg-secondaryBg rounded-2xl p-3">
                      <ContactRow kind={kind} value={c.value} label={c.label} />
                    </li>
                  ))}
              </ul>
            </div>
          ))}
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
      <span className="font-medium">{value}</span>
      {label && <span className="text-tg-hint text-xs"> · {label}</span>}
    </>
  );
  if (kind === "TELEGRAM_USERNAME") {
    return (
      <a
        href={`https://t.me/${value.replace(/^@/, "")}`}
        target="_blank"
        rel="noreferrer"
        className="text-tg-link"
      >
        {inner}
      </a>
    );
  }
  if (kind === "PHONE") {
    return (
      <a href={`tel:${value}`} className="text-tg-link">
        {inner}
      </a>
    );
  }
  if (kind === "EMAIL") {
    return (
      <a href={`mailto:${value}`} className="text-tg-link">
        {inner}
      </a>
    );
  }
  return <span>{inner}</span>;
}
