import { useState } from "react";
import { BrandVoiceTab } from "../components/settings/BrandVoiceTab";
import { BotSettingsTab } from "../components/settings/BotSettingsTab";
import { ChannelTab } from "../components/settings/ChannelTab";
import { AIAgentsTab } from "../components/settings/AIAgentsTab";
import { DmContactsTab } from "../components/settings/DmContactsTab";
import { PaymentAccountsTab } from "../components/settings/PaymentAccountsTab";

type Tab = "bot" | "channel" | "brand" | "ai" | "dm" | "payments";

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("bot");

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl sm:text-3xl font-semibold text-slate-900 mb-1">
        Telegram Settings
      </h1>
      <p className="text-slate-500 mb-6">
        Everything here applies <span className="font-medium text-slate-700">only to Telegram</span>.
      </p>

      <div className="flex gap-1 sm:gap-2 border-b border-slate-200 mb-6 overflow-x-auto">
        <TabButton active={tab === "bot"} onClick={() => setTab("bot")}>
          Telegram Bot
        </TabButton>
        <TabButton active={tab === "channel"} onClick={() => setTab("channel")}>
          Channel
        </TabButton>
        <TabButton active={tab === "brand"} onClick={() => setTab("brand")}>
          Brand Voice
        </TabButton>
        <TabButton active={tab === "ai"} onClick={() => setTab("ai")}>
          AI Agents
        </TabButton>
        <TabButton active={tab === "dm"} onClick={() => setTab("dm")}>
          DM Info
        </TabButton>
        <TabButton active={tab === "payments"} onClick={() => setTab("payments")}>
          Payment Accounts
        </TabButton>
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
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition whitespace-nowrap ${
        active
          ? "border-brand-600 text-brand-700"
          : "border-transparent text-slate-600 hover:text-slate-900"
      }`}
    >
      {children}
    </button>
  );
}
