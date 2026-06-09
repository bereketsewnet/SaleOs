import { api } from "./api";

export interface MerchantProfile {
  business_name: string;
  contact_email: string;
  contact_phone: string;
  is_active: boolean;
}

export interface MerchantProfileUpdate {
  business_name?: string;
  contact_email?: string;
  contact_phone?: string;
}

export async function getMerchantProfile(): Promise<MerchantProfile> {
  const { data } = await api.get<MerchantProfile>("/api/v1/core/merchant-profile/");
  return data;
}

export async function updateMerchantProfile(
  payload: MerchantProfileUpdate
): Promise<MerchantProfile> {
  const { data } = await api.patch<MerchantProfile>(
    "/api/v1/core/merchant-profile/",
    payload
  );
  return data;
}
