import axios from "axios";
import { getMerchantId, getWebApp, isDevMode } from "./telegram";

export const api = axios.create({
  baseURL: "/",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const merchantId = getMerchantId();
  if (merchantId) {
    config.params = { ...(config.params || {}), merchant_id: merchantId };
    config.headers["X-Merchant-Id"] = merchantId;
  }
  const wa = getWebApp();
  if (wa?.initData) {
    config.headers["X-Telegram-Init-Data"] = wa.initData;
  } else if (isDevMode()) {
    config.params = { ...(config.params || {}), dev: 1 };
  }
  return config;
});
