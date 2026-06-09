import { api } from "./api";
import type { CurrentUser } from "../store/auth";

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterPayload {
  business_name: string;
  contact_phone: string;
  contact_email: string;
  first_name: string;
  last_name: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export async function register(payload: RegisterPayload): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/api/v1/auth/register", payload);
  return data;
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/api/v1/auth/login", payload);
  return data;
}

export async function getMe(): Promise<CurrentUser> {
  const { data } = await api.get<CurrentUser>("/api/v1/auth/me");
  return data;
}

export async function logout(): Promise<void> {
  await api.post("/api/v1/auth/logout");
}
