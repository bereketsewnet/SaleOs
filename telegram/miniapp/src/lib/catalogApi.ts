import { api } from "./api";

export interface CatalogProduct {
  id: string;
  title: string;
  description: string | null;
  base_price: string | null;
  image_url: string | null;
  in_stock: number;
}

export interface CatalogProductDetail extends CatalogProduct {
  image_urls: string[];
}

export interface CatalogMerchantInfo {
  business_name: string;
  business_description: string | null;
  payment_accounts: {
    bank_name: string;
    account_number: string;
    account_holder_name: string;
    phone: string | null;
  }[];
  dm_contacts: {
    kind: "TELEGRAM_USERNAME" | "PHONE" | "EMAIL" | "ADDRESS" | "OTHER";
    value: string;
    label: string | null;
    position: number;
  }[];
}

export interface ChatMessage {
  role: "customer" | "agent";
  content: string;
}

export interface OrderItemPublic {
  product_id: string;
  title: string;
  quantity: number;
  unit_price: string;
  line_total: string;
}

export interface OrderPayment {
  bank_name: string;
  account_number: string;
  account_holder_name: string;
  phone: string | null;
}

export interface OrderDmContact {
  kind: string;
  value: string;
  label: string | null;
}

export interface Order {
  id: string;
  merchant_id: string;
  channel_source: string;
  order_status: string;
  total_amount: string;
  customer_info: Record<string, unknown> | null;
  notes: string | null;
  payment_account: OrderPayment | null;
  items: OrderItemPublic[];
  dm_contacts: OrderDmContact[];
  payment_proof_url: string | null;
  payment_proof_uploaded_at: string | null;
  payment_verified_at: string | null;
  payment_rejection_reason: string | null;
  created_at: string;
}

export async function listProducts(search?: string): Promise<CatalogProduct[]> {
  const { data } = await api.get<CatalogProduct[]>("/api/v1/catalog/products", {
    params: search ? { search } : undefined,
  });
  return data;
}

export async function getProduct(id: string): Promise<CatalogProductDetail> {
  const { data } = await api.get<CatalogProductDetail>(`/api/v1/catalog/products/${id}`);
  return data;
}

export async function getMerchantInfo(): Promise<CatalogMerchantInfo> {
  const { data } = await api.get<CatalogMerchantInfo>("/api/v1/catalog/merchant-info");
  return data;
}

export async function chat(
  message: string,
  productId?: string | null
): Promise<{ reply: string; history: ChatMessage[] }> {
  const { data } = await api.post<{ reply: string; history: ChatMessage[] }>(
    "/api/v1/catalog/chat",
    { message, product_id: productId ?? null }
  );
  return data;
}

export async function getChatHistory(productId?: string | null): Promise<ChatMessage[]> {
  const { data } = await api.get<ChatMessage[]>("/api/v1/catalog/chat", {
    params: productId ? { product_id: productId } : undefined,
  });
  return data;
}

export interface PlaceOrderPayload {
  items: { product_id: string; quantity: number }[];
  customer: { name: string; phone: string; address: string };
  notes?: string | null;
}

export async function placeOrder(payload: PlaceOrderPayload): Promise<Order> {
  const { data } = await api.post<Order>("/api/v1/catalog/orders", payload);
  return data;
}

export async function getOrder(id: string): Promise<Order> {
  const { data } = await api.get<Order>(`/api/v1/catalog/orders/${id}`);
  return data;
}

export async function uploadPaymentProof(id: string, file: File): Promise<Order> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<Order>(
    `/api/v1/catalog/orders/${id}/payment-proof`,
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}
