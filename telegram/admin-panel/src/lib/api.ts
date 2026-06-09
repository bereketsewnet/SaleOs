import axios, { AxiosError, type AxiosRequestConfig } from "axios";
import { useAuthStore } from "../store/auth";

export const api = axios.create({
  baseURL: "/",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise: Promise<string | null> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as AxiosRequestConfig & { _retry?: boolean };
    if (
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      !original.url?.includes("/auth/")
    ) {
      original._retry = true;
      refreshPromise ??= refreshAccessToken();
      const newToken = await refreshPromise;
      refreshPromise = null;
      if (newToken) {
        original.headers = { ...original.headers, Authorization: `Bearer ${newToken}` };
        return api(original);
      }
      useAuthStore.getState().clear();
    }
    return Promise.reject(error);
  }
);

async function refreshAccessToken(): Promise<string | null> {
  const refresh = useAuthStore.getState().refreshToken;
  if (!refresh) return null;
  try {
    const { data } = await axios.post("/api/v1/auth/refresh", { refresh_token: refresh });
    useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    return null;
  }
}
