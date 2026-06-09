from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class OrderItemIn(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0, le=100)


class OrderCustomerInfo(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    phone: str = Field(..., min_length=4, max_length=30)
    address: str = Field(..., min_length=1, max_length=500)


class PlaceOrderRequest(BaseModel):
    items: list[OrderItemIn] = Field(..., min_length=1)
    customer: OrderCustomerInfo
    notes: str | None = Field(default=None, max_length=1000)


class OrderItemPublic(BaseModel):
    product_id: UUID
    title: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class PaymentAccountPublic(BaseModel):
    bank_name: str
    account_number: str
    account_holder_name: str
    phone: str | None = None


class OrderDMContact(BaseModel):
    kind: str
    value: str
    label: str | None = None


class OrderPublic(BaseModel):
    id: UUID
    merchant_id: UUID
    channel_source: str
    order_status: str
    total_amount: Decimal
    customer_info: dict | None
    notes: str | None
    payment_account: PaymentAccountPublic | None = None
    items: list[OrderItemPublic] = Field(default_factory=list)
    # Convenience for Mini App success page — first active DM contact per kind
    dm_contacts: list[OrderDMContact] = Field(default_factory=list)
    # Payment receipt fields (signed URL valid for ~15 min when present)
    payment_proof_url: str | None = None
    payment_proof_uploaded_at: datetime | None = None
    payment_verified_at: datetime | None = None
    payment_rejection_reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


OrderStatusLiteral = Literal[
    "PENDING_PAYMENT",
    "PAYMENT_SUBMITTED",
    "PAYMENT_VERIFIED",
    "PAYMENT_REJECTED",
    "PREPARING",
    "SHIPPED",
    "DELIVERED",
    "CANCELLED",
]


class OrderStatusUpdate(BaseModel):
    order_status: OrderStatusLiteral


class PaymentRejectionRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)
