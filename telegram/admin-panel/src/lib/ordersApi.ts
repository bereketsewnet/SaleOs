import { api } from "./api";

export interface OrderItem {
  product_id: string;
  title: string;
  quantity: number;
  unit_price: string;
  line_total: string;
}

export interface OrderPaymentAccount {
  bank_name: string;
  account_number: string;
  account_holder_name: string;
  phone: string | null;
}

export interface Order {
  id: string;
  merchant_id: string;
  channel_source: string;
  order_status: string;
  total_amount: string;
  customer_info: Record<string, any> | null;
  notes: string | null;
  payment_account: OrderPaymentAccount | null;
  items: OrderItem[];
  payment_proof_url: string | null;
  payment_proof_uploaded_at: string | null;
  payment_verified_at: string | null;
  payment_rejection_reason: string | null;
  created_at: string;
}

export type OrderStatus =
  | "PENDING_PAYMENT"
  | "PAYMENT_SUBMITTED"
  | "PAYMENT_VERIFIED"
  | "PAYMENT_REJECTED"
  | "PREPARING"
  | "SHIPPED"
  | "DELIVERED"
  | "CANCELLED";

export const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  PENDING_PAYMENT: "Awaiting payment",
  PAYMENT_SUBMITTED: "Receipt submitted",
  PAYMENT_VERIFIED: "Payment verified",
  PAYMENT_REJECTED: "Receipt rejected",
  PREPARING: "Preparing",
  SHIPPED: "Shipped",
  DELIVERED: "Delivered",
  CANCELLED: "Cancelled",
};

export const ORDER_STATUS_FLOW: OrderStatus[] = [
  "PENDING_PAYMENT",
  "PAYMENT_SUBMITTED",
  "PAYMENT_VERIFIED",
  "PREPARING",
  "SHIPPED",
  "DELIVERED",
];

export async function listOrders(filters?: {
  status_eq?: OrderStatus;
  channel_eq?: string;
}): Promise<Order[]> {
  const { data } = await api.get<Order[]>("/api/v1/core/orders/", { params: filters });
  return data;
}

export async function getOrder(id: string): Promise<Order> {
  const { data } = await api.get<Order>(`/api/v1/core/orders/${id}`);
  return data;
}

export async function updateOrderStatus(id: string, order_status: OrderStatus): Promise<Order> {
  const { data } = await api.patch<Order>(`/api/v1/core/orders/${id}/status`, { order_status });
  return data;
}

export async function verifyPayment(id: string): Promise<Order> {
  const { data } = await api.patch<Order>(`/api/v1/core/orders/${id}/verify-payment`);
  return data;
}

export async function rejectPayment(id: string, reason: string): Promise<Order> {
  const { data } = await api.patch<Order>(`/api/v1/core/orders/${id}/reject-payment`, { reason });
  return data;
}
