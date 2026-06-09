/**
 * Telegram WebApp SDK helper. Wraps `window.Telegram.WebApp` and provides:
 * - init / theme application
 * - merchant_id resolver (from URL or initDataUnsafe.start_param)
 * - dev mode detection (for local browser preview)
 * - typed MainButton + BackButton + HapticFeedback helpers
 */

type TgWebApp = typeof window.Telegram.WebApp;

let _webApp: TgWebApp | null = null;

export function getWebApp(): TgWebApp | null {
  if (_webApp !== null) return _webApp;
  if (typeof window !== "undefined" && window.Telegram?.WebApp) {
    _webApp = window.Telegram.WebApp;
    return _webApp;
  }
  return null;
}

export function isInTelegram(): boolean {
  return !!getWebApp()?.initData;
}

const SS_KEY_MERCHANT = "saleos-merchant-id";
const SS_KEY_DEV = "saleos-dev-mode";

export function isDevMode(): boolean {
  if (isInTelegram()) return false;
  const params = new URLSearchParams(window.location.search);
  if (params.get("dev") === "1") {
    try {
      localStorage.setItem(SS_KEY_DEV, "1");
    } catch {
      /* ignore */
    }
    return true;
  }
  try {
    return localStorage.getItem(SS_KEY_DEV) === "1";
  } catch {
    return false;
  }
}

export function getMerchantId(): string | null {
  // 1. URL param (?merchant_id=...) — first visit, deep link, refresh on a page that has it.
  const params = new URLSearchParams(window.location.search);
  const fromUrl = params.get("merchant_id");
  if (fromUrl) {
    try {
      localStorage.setItem(SS_KEY_MERCHANT, fromUrl);
    } catch {
      /* ignore */
    }
    return fromUrl;
  }
  // 2. Telegram start_param like "merchant_<uuid>"
  const startParam = getWebApp()?.initDataUnsafe?.start_param ?? "";
  if (startParam.startsWith("merchant_")) {
    const id = startParam.slice("merchant_".length);
    try {
      localStorage.setItem(SS_KEY_MERCHANT, id);
    } catch {
      /* ignore */
    }
    return id;
  }
  // 3. Cached from a previous navigation in this session
  try {
    const cached = localStorage.getItem(SS_KEY_MERCHANT);
    if (cached) return cached;
  } catch {
    /* ignore */
  }
  return null;
}

export function getStartProductId(): string | null {
  const params = new URLSearchParams(window.location.search);
  const fromUrl = params.get("product_id");
  if (fromUrl) return fromUrl;
  const startParam = getWebApp()?.initDataUnsafe?.start_param ?? "";
  if (startParam.startsWith("product_")) return startParam.slice("product_".length);
  return null;
}

export function initTelegramApp(): void {
  const wa = getWebApp();
  if (wa) {
    try {
      wa.ready();
      wa.expand();
    } catch {
      // ignore
    }
  }
  applyTelegramTheme();
}

export function applyTelegramTheme(): void {
  const wa = getWebApp();
  const params = wa?.themeParams ?? ({} as Record<string, string>);
  const root = document.documentElement;
  const map: Record<string, string | undefined> = {
    "--tg-bg": params.bg_color,
    "--tg-text": params.text_color,
    "--tg-hint": params.hint_color,
    "--tg-link": params.link_color,
    "--tg-button": params.button_color,
    "--tg-button-text": params.button_text_color,
    "--tg-secondary-bg": params.secondary_bg_color,
  };
  for (const [k, v] of Object.entries(map)) {
    if (v) root.style.setProperty(k, v);
  }
  if (wa?.colorScheme === "dark") {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
}

// ---- MainButton helper ----
interface MainButtonOptions {
  text: string;
  onClick: () => void;
  enabled?: boolean;
  loading?: boolean;
}

export function useMainButton(opts: MainButtonOptions | null) {
  const wa = getWebApp();
  if (!wa?.MainButton) return;
  if (opts === null) {
    wa.MainButton.hide();
    return;
  }
  wa.MainButton.setText(opts.text);
  if (opts.loading) wa.MainButton.showProgress(false);
  else wa.MainButton.hideProgress();
  if (opts.enabled === false) wa.MainButton.disable();
  else wa.MainButton.enable();
  wa.MainButton.show();
  wa.MainButton.onClick(opts.onClick);
}

export function clearMainButton(handler?: () => void) {
  const wa = getWebApp();
  if (!wa?.MainButton) return;
  if (handler) wa.MainButton.offClick(handler);
  wa.MainButton.hide();
  wa.MainButton.hideProgress();
}

export function hapticImpact(style: "light" | "medium" | "heavy" = "light") {
  getWebApp()?.HapticFeedback?.impactOccurred(style);
}
export function hapticNotification(type: "success" | "warning" | "error" = "success") {
  getWebApp()?.HapticFeedback?.notificationOccurred(type);
}
