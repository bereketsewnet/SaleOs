import { api } from "./api";

export interface TelegramChannelStatus {
  connected: boolean;
  channel_id: number | null;
  channel_username: string | null;
  channel_title: string | null;
}

export interface TelegramChannelPost {
  id: string;
  channel_id: number;
  message_id: number;
  caption: string | null;
  photo_file_id: string | null;
  posted_by_admin: boolean;
  product_id: string | null;
  posted_at: string;
}

export async function getChannelStatus(): Promise<TelegramChannelStatus> {
  const { data } = await api.get<TelegramChannelStatus>(
    "/api/v1/core/telegram-channel/status"
  );
  return data;
}

export async function unbindChannel(): Promise<void> {
  await api.delete("/api/v1/core/telegram-channel/unbind");
}

export async function listChannelPosts(limit = 15): Promise<TelegramChannelPost[]> {
  const { data } = await api.get<TelegramChannelPost[]>(
    "/api/v1/core/telegram-channel/posts",
    { params: { limit } }
  );
  return data;
}
