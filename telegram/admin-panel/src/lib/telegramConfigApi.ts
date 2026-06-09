import { api } from "./api";

export type LanguagePref = "AMHARIC" | "ENGLISH" | "AUTO";
export type BusinessMode = "PRODUCT_SALES" | "SERVICE_INQUIRY";

export interface TelegramBotConfig {
  id: string;
  merchant_id: string;
  bot_username: string | null;
  discussion_group_id: number | null;
  welcome_message: string | null;
  language_preference: LanguagePref;
  is_active: boolean;
  updated_at: string;
  // Telegram-specific brand voice
  business_type: string | null;
  business_description: string | null;
  system_prompt: string | null;
  business_mode: BusinessMode;
  // Defaults inherited by every product whose own fields are blank
  default_product_identifier: string | null;
  default_product_instructions: string | null;
}

export interface TelegramBotConfigUpsert {
  bot_token: string;
  language_preference: LanguagePref;
  welcome_message?: string | null;
}

export interface TelegramBrandVoiceUpdate {
  business_type?: string | null;
  business_description?: string | null;
  system_prompt?: string | null;
  business_mode?: BusinessMode | null;
  default_product_identifier?: string | null;
  default_product_instructions?: string | null;
}

export interface TelegramPresets {
  business_types: string[];
}

export async function getTelegramConfig(): Promise<TelegramBotConfig | null> {
  const { data } = await api.get<TelegramBotConfig | null>("/api/v1/core/telegram-config/");
  return data;
}

export async function upsertTelegramConfig(
  payload: TelegramBotConfigUpsert
): Promise<TelegramBotConfig> {
  const { data } = await api.put<TelegramBotConfig>("/api/v1/core/telegram-config/", payload);
  return data;
}

export async function updateTelegramBrandVoice(
  payload: TelegramBrandVoiceUpdate
): Promise<TelegramBotConfig> {
  const { data } = await api.patch<TelegramBotConfig>(
    "/api/v1/core/telegram-config/brand-voice",
    payload
  );
  return data;
}

export async function getTelegramPresets(): Promise<TelegramPresets> {
  const { data } = await api.get<TelegramPresets>("/api/v1/core/telegram-config/presets");
  return data;
}

export async function deleteTelegramConfig(): Promise<void> {
  await api.delete("/api/v1/core/telegram-config/");
}
