import { api } from "./api";

export type AIProvider = "GEMINI" | "OPENAI" | "CLAUDE";

export interface TelegramAISettings {
  ai_provider: AIProvider | null;
  ai_api_key_set: boolean;
  ai_model: string | null;
  ai_auto_reply_dm: boolean;
  ai_auto_reply_comments: boolean;
  ai_parse_hashtag_products: boolean;
}

export interface TelegramAISettingsUpdate {
  ai_provider?: AIProvider | null;
  ai_api_key?: string | null;
  ai_model?: string | null;
  ai_auto_reply_dm?: boolean | null;
  ai_auto_reply_comments?: boolean | null;
  ai_parse_hashtag_products?: boolean | null;
}

export const PROVIDER_LABELS: Record<AIProvider, string> = {
  GEMINI: "Google Gemini",
  OPENAI: "OpenAI (GPT)",
  CLAUDE: "Anthropic Claude",
};

export const DEFAULT_MODELS: Record<AIProvider, string> = {
  GEMINI: "gemini-2.0-flash",
  OPENAI: "gpt-4.1-mini",
  CLAUDE: "claude-haiku-4-5-20251001",
};

export async function getTelegramAISettings(): Promise<TelegramAISettings | null> {
  const { data } = await api.get<TelegramAISettings | null>(
    "/api/v1/core/telegram-config/ai"
  );
  return data;
}

export async function updateTelegramAISettings(
  payload: TelegramAISettingsUpdate
): Promise<TelegramAISettings> {
  const { data } = await api.patch<TelegramAISettings>(
    "/api/v1/core/telegram-config/ai",
    payload
  );
  return data;
}
