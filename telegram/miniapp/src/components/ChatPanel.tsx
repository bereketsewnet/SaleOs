import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
    <div className="fixed inset-0 z-50 bg-black/30 flex flex-col" onClick={onClose}>
      <div className="mt-auto bg-tg-bg rounded-t-3xl flex flex-col h-[85vh]" onClick={(e) => e.stopPropagation()}>
        <header className="p-3 border-b border-black/10 flex items-center justify-between">
          <h2 className="font-semibold">Ask about this product</h2>
          <button onClick={onClose} className="text-tg-hint text-2xl leading-none">×</button>
        </header>

        <div ref={listRef} className="flex-1 overflow-y-auto p-3 space-y-2">
          {isLoading ? (
            <p className="text-sm text-tg-hint">Loading…</p>
          ) : history.length === 0 ? (
            <p className="text-sm text-tg-hint text-center mt-6">
              Ask anything about this product. We reply with our shop info, price, and how to pay.
            </p>
          ) : (
            history.map((m, i) => <Bubble key={i} message={m} />)
          )}
          {sendMutation.isPending && (
            <div className="text-sm text-tg-hint italic">typing…</div>
          )}
        </div>

        <div className="px-3 pt-2 pb-1 flex gap-2 overflow-x-auto no-scrollbar">
          {onAddToCart && (
            <button
              onClick={() => {
                hapticImpact("light");
                onAddToCart();
              }}
              className="shrink-0 px-3 py-1.5 rounded-full bg-tg-secondaryBg text-xs font-medium border border-black/10"
            >
              🛒 Add to cart
            </button>
          )}
          <button
            onClick={() => {
              hapticImpact("light");
              navigate(withSearch("/cart"));
            }}
            className="shrink-0 px-3 py-1.5 rounded-full bg-tg-secondaryBg text-xs font-medium border border-black/10"
          >
            🧾 Checkout
          </button>
          <button
            onClick={() => {
              hapticImpact("light");
              navigate(withSearch("/info"));
            }}
            className="shrink-0 px-3 py-1.5 rounded-full bg-tg-secondaryBg text-xs font-medium border border-black/10"
          >
            💳 Bank & Contacts
          </button>
        </div>

        <div className="p-3 border-t border-black/10 flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") send();
            }}
            placeholder="Type a message…"
            className="flex-1 rounded-xl bg-tg-secondaryBg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-tg-link/50"
          />
          <button
            onClick={send}
            disabled={!input.trim() || sendMutation.isPending}
            className="px-4 py-2 rounded-xl bg-tg-button text-tg-buttonText font-medium text-sm disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

function Bubble({ message }: { message: ChatMessage }) {
  const isCustomer = message.role === "customer";
  return (
    <div className={`flex ${isCustomer ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm whitespace-pre-wrap ${
          isCustomer ? "bg-tg-button text-tg-buttonText" : "bg-tg-secondaryBg"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}
