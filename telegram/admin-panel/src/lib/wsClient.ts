/**
 * Tiny auto-reconnecting WebSocket helper for /ws/alerts.
 * Usage:
 *   const ws = subscribeAlerts({ token, onMessage });
 *   ws.close(); // when component unmounts
 */
export interface AlertMessage {
  type: string;
  payload: Record<string, any>;
}

export function subscribeAlerts(opts: {
  token: string;
  onMessage: (msg: AlertMessage) => void;
  onOpen?: () => void;
}): { close: () => void } {
  let stopped = false;
  let ws: WebSocket | null = null;
  let retryMs = 1000;

  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${proto}//${window.location.host}/ws/alerts?token=${encodeURIComponent(opts.token)}`;

  function connect() {
    if (stopped) return;
    try {
      ws = new WebSocket(url);
    } catch {
      scheduleRetry();
      return;
    }
    ws.onopen = () => {
      retryMs = 1000;
      opts.onOpen?.();
    };
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data && typeof data === "object" && "type" in data) {
          opts.onMessage(data as AlertMessage);
        }
      } catch {
        // ignore non-JSON
      }
    };
    ws.onerror = () => {
      try {
        ws?.close();
      } catch {
        // ignore
      }
    };
    ws.onclose = () => {
      if (!stopped) scheduleRetry();
    };
  }

  function scheduleRetry() {
    if (stopped) return;
    setTimeout(connect, retryMs);
    retryMs = Math.min(retryMs * 2, 15000);
  }

  connect();

  return {
    close() {
      stopped = true;
      try {
        ws?.close();
      } catch {
        // ignore
      }
    },
  };
}
