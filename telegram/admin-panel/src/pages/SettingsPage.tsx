import { useState } from "react";
import {
  HiOutlineCog6Tooth,
  HiOutlineRadio,
  HiOutlineMegaphone,
  HiOutlineSparkles,
  HiOutlineChatBubbleLeftRight,
  HiOutlineBanknotes,
} from "react-icons/hi2";
import { BrandVoiceTab } from "../components/settings/BrandVoiceTab";
import { BotSettingsTab } from "../components/settings/BotSettingsTab";
import { ChannelTab } from "../components/settings/ChannelTab";
import { AIAgentsTab } from "../components/settings/AIAgentsTab";
import { DmContactsTab } from "../components/settings/DmContactsTab";
import { PaymentAccountsTab } from "../components/settings/PaymentAccountsTab";

type TabId = "bot" | "channel" | "brand" | "ai" | "dm" | "payments";

const TABS: {
  id: TabId;
  label: string;
  Icon: React.ComponentType<{ className?: string }>;
}[] = [
  { id: "bot", label: "Telegram Bot", Icon: HiOutlineRadio },
  { id: "channel", label: "Channel", Icon: HiOutlineMegaphone },
  { id: "brand", label: "Brand Voice", Icon: HiOutlineSparkles },
  { id: "ai", label: "AI Agents", Icon: HiOutlineCog6Tooth },
  { id: "dm", label: "DM Info", Icon: HiOutlineChatBubbleLeftRight },
  { id: "payments", label: "Payment Accounts", Icon: HiOutlineBanknotes },
];

export default function SettingsPage() {
  const [tab, setTab] = useState<TabId>("bot");

  return (
    <div className="max-w-5xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">Telegram Settings</h1>
        <p className="text-slate-500 text-sm mt-1">
          Everything here applies <span className="font-semibold text-slate-700">only to Telegram</span>.
          TikTok, IG and FB have their own settings on their own panels.
        </p>
      </div>

      <div className="card mb-5 p-1.5 inline-flex flex-wrap gap-1 max-w-full overflow-x-auto scroll-thin">
        {TABS.map((t) => (
          <TabButton
            key={t.id}
            active={tab === t.id}
            onClick={() => setTab(t.id)}
            Icon={t.Icon}
            label={t.label}
          />
        ))}
      </div>

      {tab === "bot" && <BotSettingsTab />}
      {tab === "channel" && <ChannelTab />}
      {tab === "brand" && <BrandVoiceTab />}
      {tab === "ai" && <AIAgentsTab />}
      {tab === "dm" && <DmContactsTab />}
      {tab === "payments" && <PaymentAccountsTab />}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  Icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  Icon: React.ComponentType<{ className?: string }>;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-semibold transition whitespace-nowrap ${
        active
          ? "bg-brand-600 text-white shadow-sm"
          : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
      }`}
    >
      <Icon className="w-4 h-4" />
      {label}
    </button>
  );
}
