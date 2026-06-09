import { api } from "./api";

export interface Product {
  id: string;
  merchant_id: string;
  title: string;
  description: string | null;
  base_price: string | null;
  sku: string | null;
  image_urls: string[];
  quantity: number;
  reserved_quantity: number;
  is_published_to_channel: boolean;
  identifier: string | null;
  instructions: string | null;
  is_ocr_identified: boolean;
  created_at: string;
}

export interface ProductCreate {
  title: string;
  description?: string | null;
  base_price?: string | null;
  sku?: string | null;
  image_urls: string[];
  initial_stock: number;
  publish_to_channel: boolean;
  identifier?: string | null;
  instructions?: string | null;
  run_ocr?: boolean;
}

export interface ProductUpdate {
  title?: string;
  description?: string | null;
  base_price?: string;
  sku?: string;
  image_urls?: string[];
  identifier?: string | null;
  instructions?: string | null;
}

export async function runOcr(id: string): Promise<void> {
  await api.post(`/api/v1/core/products/${id}/run-ocr`);
}

export interface UploadedImage {
  url: string;
  bucket: string;
  object_key: string;
}

export async function listProducts(search?: string): Promise<Product[]> {
  const { data } = await api.get<Product[]>("/api/v1/core/products/", {
    params: search ? { search } : undefined,
  });
  return data;
}

export async function getProduct(id: string): Promise<Product> {
  const { data } = await api.get<Product>(`/api/v1/core/products/${id}`);
  return data;
}

export async function createProduct(payload: ProductCreate): Promise<Product> {
  const { data } = await api.post<Product>("/api/v1/core/products/", payload);
  return data;
}

export async function updateProduct(
  id: string,
  payload: ProductUpdate
): Promise<Product> {
  const { data } = await api.patch<Product>(`/api/v1/core/products/${id}`, payload);
  return data;
}

export interface DeleteSummary {
  channel_messages_total: number;
  channel_messages_deleted: number;
  channel_messages_failed: number;
  channel_reason: "missing_delete_permission" | "already_gone" | "unknown" | "bot_not_running" | null;
}

export async function deleteProduct(id: string): Promise<DeleteSummary> {
  const { data } = await api.delete<DeleteSummary>(`/api/v1/core/products/${id}`);
  return data;
}

export async function publishProductToChannel(id: string): Promise<void> {
  await api.post(`/api/v1/core/products/${id}/publish-to-channel`);
}

export async function uploadProductImage(file: File): Promise<UploadedImage> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<UploadedImage>(
    "/api/v1/core/products/upload-image",
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}
