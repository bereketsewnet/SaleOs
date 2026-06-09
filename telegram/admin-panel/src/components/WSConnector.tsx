import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { subscribeAlerts } from "../lib/wsClient";
import { useAlerts } from "../store/alerts";
import { useAuthStore } from "../store/auth";

/**
 * Mounted once at the App root after authentication. Opens the alerts
 * WebSocket and pushes toasts + invalidates relevant React-Query caches.
 */
export function WSConnector() {
  const token = useAuthStore((s) => s.accessToken);
  const push = useAlerts((s) => s.push);
  const qc = useQueryClient();

  useEffect(() => {
    if (!token) return;
    const sub = subscribeAlerts({
      token,
      onMessage: (msg) => {
        const orderId = msg.payload?.order_id;
        const link = orderId ? `/orders/${orderId}` : "/orders";
        if (msg.type === "NEW_ORDER") {
          push({
            type: "NEW_ORDER",
            title: "New order received",
            description: `${msg.payload.customer_name ?? "Customer"} · ETB ${msg.payload.total ?? "?"}`,
            link,
          });
          qc.invalidateQueries({ queryKey: ["orders"] });
        } else if (msg.type === "PAYMENT_SUBMITTED") {
          const fromComment = msg.payload?.source === "channel_comment";
          push({
            type: "PAYMENT_SUBMITTED",
            title: fromComment
              ? "Receipt posted in channel comments"
              : "Payment receipt submitted",
            description: `${msg.payload.customer_name ?? "Customer"} · ETB ${msg.payload.total ?? "?"} — awaiting verification`,
            link,
          });
          qc.invalidateQueries({ queryKey: ["orders"] });
          if (orderId) qc.invalidateQueries({ queryKey: ["order", orderId] });
        } else if (msg.type === "PAYMENT_VERIFIED" || msg.type === "PAYMENT_REJECTED") {
          qc.invalidateQueries({ queryKey: ["orders"] });
          if (orderId) qc.invalidateQueries({ queryKey: ["order", orderId] });
        }
      },
    });
    return () => sub.close();
  }, [token, push, qc]);

  return null;
}
