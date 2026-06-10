import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  HiOutlineXMark,
  HiOutlineShoppingCart,
  HiOutlineDocumentText,
  HiOutlineBuildingLibrary,
  HiOutlinePaperAirplane,
  HiOutlineSparkles,
} from "react-icons/hi2";
import { chat, getChatHistory, type ChatMessage } from "../lib/catalogApi";
import { hapticImpact } from "../lib/telegram";
import { withSearch } from "../lib/nav";

export function ChatPanel({
  productId,
  onClose,
  onAddToCart,
}: {
  productId: string | null;
  onClose: () => void;
  onAddToCart?: () => void;
}) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { data: history = [], isLoading } = useQuery({
    queryKey: ["chat", productId ?? "general"],
    queryFn: () => getChatHistory(productId),
  });
  const [input, setInput] = useState("");
  const listRef = useRef<HTMLDivElement>(null);

  const sendMutation = useMutation({
    mutationFn: (message: string) => chat(message, productId),
    onSuccess: (resp) => {
      qc.setQueryData<ChatMessage[]>(["chat", productId ?? "general"], resp.history);
    },
  });

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [history, sendMutation.isPending]);

  function send() {
    const text = input.trim();
    if (!text || sendMutation.isPending) return;
    hapticImpact("light");
    sendMutation.mutate(text);
    setInput("");
  }

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex flex-col animate-fade-in"
      onClick={onClose}
    >
      <div
        className="mt-auto bg-tg-bg rounded-t-3xl flex flex-col h-[88vh] shadow-lg animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drag handle */}
        <div className="w-12 h-1.5 rounded-full bg-slate-300 mx-auto mt-2" />

        <header className="px-4 pt-3 pb-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 grid place-items-center text-white">
              <HiOutlineSparkles className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-bold text-tg-text leading-tight">AI Assistant</p>
              <p className="text-[11px] text-tg-hint">Ask anything about this product</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-tg-hint hover:text-tg-text p-1.5 hover:bg-tg-secondaryBg rounded-lg transition"
            aria-label="Close chat"
          >
            <HiOutlineXMark className="w-5 h-5" />
          </button>
        </header>

        <div ref={listRef} className="flex-1 overflow-y-auto px-3 py-2 space-y-2 scroll-thin">
          {isLoading ? (
            <p className="text-sm text-tg-hint">Loading…</p>
          ) : history.length === 0 ? (
            <div className="text-center mt-8 px-4">
              <div className="w-14 h-14 rounded-2xl bg-brand-50 grid place-items-center text-brand-600 mx-auto mb-3">
                <HiOutlineSparkles className="w-7 h-7" />
              </div>
              <p className="text-sm font-semibold text-tg-text">Ask me anything</p>
              <p className="text-xs text-tg-hint mt-1">
                I know the product details, prices, and how to pay.
              </p>
            </div>
          ) : (
            history.map((m, i) => <Bubble key={i} message={m} />)
          )}
          {sendMutation.isPending && (
            <div className="flex">
              <div className="bg-tg-secondaryBg rounded-2xl px-3 py-2 text-sm text-tg-hint italic flex items-center gap-1.5">
                <span className="flex gap-0.5">
                  <Dot delay={0} />
                  <Dot delay={150} />
                  <Dot delay={300} />
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Quick-action chips */}
        <div className="px-3 pt-2 pb-1 flex gap-2 overflow-x-auto no-scrollbar">
          {onAddToCart && (
            <Chip
              onClick={() => {
                hapticImpact("light");
                onAddToCart();
              }}
              Icon={HiOutlineShoppingCart}
              label="Add to cart"
            />
          )}
          <Chip
            onClick={() => {
              hapticImpact("light");
              navigate(withSearch("/cart"));
            }}
            Icon={HiOutlineDocumentText}
            label="Checkout"
          />
          <Chip
            onClick={() => {
              hapticImpact("light");
              navigate(withSearch("/info"));
            }}
            Icon={HiOutlineBuildingLibrary}
            label="Bank & contacts"
          />
        </div>

        <div className="px-3 pt-2 pb-[max(env(safe-area-inset-bottom),0.75rem)] flex gap-2 bg-tg-bg">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") send();
            }}
            placeholder="Type a message…"
            className="input flex-1"
          />
          <button
            onClick={send}
            disabled={!input.trim() || sendMutation.isPending}
            className="w-12 h-12 rounded-2xl bg-tg-button text-tg-buttonText grid place-items-center disabled:opacity-50 active:scale-95 transition"
            aria-label="Send"
          >
            <HiOutlinePaperAirplane className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}

function Chip({
  onClick,
  Icon,
  label,
}: {
  onClick: () => void;
  Icon: React.ComponentType<{ className?: string }>;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-tg-secondaryBg text-xs font-semibold text-slate-700 hover:bg-slate-200 active:scale-95 transition"
    >
      <Icon className="w-3.5 h-3.5" />
      {label}
    </button>
  );
}

function Bubble({ message }: { message: ChatMessage }) {
  const isCustomer = message.role === "customer";
  return (
    <div className={`flex ${isCustomer ? "justify-end" : "justify-start"} animate-fade-in`}>
      <div
        className={`max-w-[82%] rounded-2xl px-3.5 py-2 text-sm whitespace-pre-wrap leading-relaxed ${
          isCustomer
            ? "bg-tg-button text-tg-buttonText rounded-br-sm"
            : "bg-tg-secondaryBg text-tg-text rounded-bl-sm"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}

function Dot({ delay }: { delay: number }) {
  return (
    <span
      className="w-1.5 h-1.5 rounded-full bg-tg-hint animate-bounce"
      style={{ animationDelay: `${delay}ms` }}
    />
  );
}
