import { api } from "./api";

export interface PaymentAccount {
  id: string;
  merchant_id: string;
  bank_name: string;
  account_number: string;
  account_holder_name: string;
  phone: string | null;
  is_active: boolean;
  created_at: string;
}

export interface PaymentAccountCreate {
  bank_name: string;
  account_number: string;
  account_holder_name: string;
  phone?: string | null;
}

export interface PaymentAccountUpdate extends Partial<PaymentAccountCreate> {
  is_active?: boolean;
}

export async function listPaymentAccounts(): Promise<PaymentAccount[]> {
  const { data } = await api.get<PaymentAccount[]>("/api/v1/core/payment-accounts/");
  return data;
}

export async function createPaymentAccount(
  payload: PaymentAccountCreate
): Promise<PaymentAccount> {
  const { data } = await api.post<PaymentAccount>("/api/v1/core/payment-accounts/", payload);
  return data;
}

export async function updatePaymentAccount(
  id: string,
  payload: PaymentAccountUpdate
): Promise<PaymentAccount> {
  const { data } = await api.patch<PaymentAccount>(
    `/api/v1/core/payment-accounts/${id}`,
    payload
  );
  return data;
}

export async function deletePaymentAccount(id: string): Promise<void> {
  await api.delete(`/api/v1/core/payment-accounts/${id}`);
}
