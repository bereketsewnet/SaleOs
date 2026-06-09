import { api } from "./api";

export type DMContactKind =
  | "TELEGRAM_USERNAME"
  | "PHONE"
  | "EMAIL"
  | "ADDRESS"
  | "OTHER";

export interface DMContact {
  id: string;
  merchant_id: string;
  kind: DMContactKind;
  value: string;
  label: string | null;
  position: number;
  is_active: boolean;
  created_at: string;
}

export interface DMContactCreate {
  kind: DMContactKind;
  value: string;
  label?: string | null;
  position?: number;
  is_active?: boolean;
}

export interface DMContactUpdate {
  kind?: DMContactKind;
  value?: string;
  label?: string | null;
  position?: number;
  is_active?: boolean;
}

export const KIND_LABELS: Record<DMContactKind, string> = {
  TELEGRAM_USERNAME: "Telegram usernames",
  PHONE: "Phone numbers",
  EMAIL: "Emails",
  ADDRESS: "Addresses",
  OTHER: "Other info",
};

export const KIND_PLACEHOLDERS: Record<DMContactKind, string> = {
  TELEGRAM_USERNAME: "@yourname",
  PHONE: "+251911000000",
  EMAIL: "you@example.com",
  ADDRESS: "Bole, Addis Ababa",
  OTHER: "Custom info",
};

export async function listDMContacts(): Promise<DMContact[]> {
  const { data } = await api.get<DMContact[]>("/api/v1/core/telegram-dm-contacts/");
  return data;
}

export async function createDMContact(payload: DMContactCreate): Promise<DMContact> {
  const { data } = await api.post<DMContact>(
    "/api/v1/core/telegram-dm-contacts/",
    payload
  );
  return data;
}

export async function updateDMContact(
  id: string,
  payload: DMContactUpdate
): Promise<DMContact> {
  const { data } = await api.patch<DMContact>(
    `/api/v1/core/telegram-dm-contacts/${id}`,
    payload
  );
  return data;
}

export async function deleteDMContact(id: string): Promise<void> {
  await api.delete(`/api/v1/core/telegram-dm-contacts/${id}`);
}

export async function reorderDMContacts(
  items: { id: string; position: number }[]
): Promise<void> {
  await api.post("/api/v1/core/telegram-dm-contacts/reorder", items);
}
