"""Order placement + listing. Uses pessimistic locking on inventory_ledger to
prevent overselling, and publishes a WS alert on success so the admin panel
gets a real-time toast."""
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import httpx
import structlog

from app.core.config import settings
from app.core.redis import get_redis
from app.models.order import ChannelSource, Order, OrderStatus
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.payment_account_repository import PaymentAccountRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.telegram_dm_contact_repository import (
    TelegramDMContactRepository,
)
from app.schemas.order import (
    OrderCustomerInfo,
    OrderDMContact,
    OrderItemIn,
    OrderItemPublic,
    OrderPublic,
    PaymentAccountPublic,
)
from app.services.media_service import ReceiptStorage
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


def _customer_status_message(order: Order, status: str) -> str | None:
    short_id = str(order.id)[:8]
    if status == OrderStatus.PREPARING:
        return f"🛠 Order #{short_id} is being prepared. We'll let you know when it ships."
    if status == OrderStatus.SHIPPED:
        return f"🚚 Order #{short_id} is on its way to you."
    if status == OrderStatus.DELIVERED:
        return f"📦 Order #{short_id} is marked as delivered. Thanks for shopping with us!"
    if status == OrderStatus.CANCELLED:
        return f"⚠️ Order #{short_id} was cancelled. If you have questions, reply here."
    return None


class OutOfStockError(Exception):
    def __init__(self, product_id: UUID, requested: int, available: int) -> None:
        super().__init__(f"out_of_stock for {product_id}: requested {requested}, available {available}")
        self.product_id = product_id
        self.requested = requested
        self.available = available


class OrderNotFoundError(Exception):
    pass


class ProductMissingError(Exception):
    pass


class OrderService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.orders = OrderRepository(db)
        self.products = ProductRepository(db)
        self.inventory = InventoryRepository(db)
        self.payments = PaymentAccountRepository(db)
        self.contacts = TelegramDMContactRepository(db)

    async def place_order(
        self,
        *,
        merchant_id: UUID,
        telegram_user_id: int,
        items: list[OrderItemIn],
        customer: OrderCustomerInfo,
        notes: str | None,
    ) -> OrderPublic:
        # 1. Lock inventory rows + collect (product, qty, unit_price) for the order.
        priced_items: list[dict] = []
        product_titles: dict[UUID, str] = {}
        total = Decimal("0")
        for it in items:
            product = await self.products.get(it.product_id, merchant_id)
            if not product:
                raise ProductMissingError(str(it.product_id))
            ledger = await self.inventory.get_for_update(it.product_id)
            available = (ledger.quantity - ledger.reserved_quantity) if ledger else 0
            if available < it.quantity:
                raise OutOfStockError(it.product_id, it.quantity, available)
            # Reserve.
            if ledger:
                ledger.reserved_quantity += it.quantity
            unit_price = product.base_price or Decimal("0")
            line_total = Decimal(str(unit_price)) * Decimal(it.quantity)
            total += line_total
            priced_items.append(
                {
                    "product_id": it.product_id,
                    "quantity": it.quantity,
                    "unit_price": unit_price,
                }
            )
            product_titles[it.product_id] = product.title

        # 2. Default payment account (active only, oldest first).
        payment_account = await self.payments.get_default(merchant_id)
        payment_account_id = payment_account.id if payment_account else None

        # 3. Persist Order + items.
        customer_info = {
            "name": customer.name,
            "phone": customer.phone,
            "address": customer.address,
            "telegram_user_id": telegram_user_id,
        }
        order = await self.orders.create_with_items(
            merchant_id=merchant_id,
            channel_source=ChannelSource.TELEGRAM,
            customer_info=customer_info,
            notes=notes,
            total_amount=total,
            order_status=OrderStatus.PENDING_PAYMENT,
            payment_account_id=payment_account_id,
            items=priced_items,
        )

        # 4. Fire the WS alert (best-effort).
        try:
            await self._publish_alert(
                merchant_id,
                "NEW_ORDER",
                {
                    "order_id": str(order.id),
                    "total": str(total),
                    "customer_name": customer.name,
                },
            )
        except Exception as exc:
            logger.warning("ws_alert_publish_failed", error=str(exc))

        # 5. Build the response (Mini App success page needs payment + DM contacts).
        contacts = await self.contacts.list_active(merchant_id)
        # First active per kind, in a stable kind order.
        kind_order = ["TELEGRAM_USERNAME", "PHONE", "EMAIL", "ADDRESS", "OTHER"]
        first_per_kind: list[OrderDMContact] = []
        for kind in kind_order:
            for c in contacts:
                if c.kind == kind:
                    first_per_kind.append(
                        OrderDMContact(kind=c.kind, value=c.value, label=c.label)
                    )
                    break

        return OrderPublic(
            id=order.id,
            merchant_id=order.merchant_id,
            channel_source=order.channel_source,
            order_status=order.order_status,
            total_amount=order.total_amount,
            customer_info=order.customer_info,
            notes=order.notes,
            payment_account=PaymentAccountPublic(
                bank_name=payment_account.bank_name,
                account_number=payment_account.account_number,
                account_holder_name=payment_account.account_holder_name,
                phone=payment_account.phone,
            ) if payment_account else None,
            items=[
                OrderItemPublic(
                    product_id=it["product_id"],
                    title=product_titles[it["product_id"]],
                    quantity=it["quantity"],
                    unit_price=Decimal(str(it["unit_price"])),
                    line_total=Decimal(str(it["unit_price"])) * Decimal(it["quantity"]),
                )
                for it in priced_items
            ],
            dm_contacts=first_per_kind,
            created_at=order.created_at,
        )

    async def list_for_merchant(
        self, merchant_id: UUID, **filters
    ) -> list[Order]:
        return await self.orders.list_for_merchant(merchant_id, **filters)

    async def get_for_merchant(
        self, order_id: UUID, merchant_id: UUID
    ) -> Order:
        order = await self.orders.get_scoped(order_id, merchant_id)
        if not order:
            raise OrderNotFoundError()
        return order

    async def update_status(
        self, order_id: UUID, merchant_id: UUID, new_status: str
    ) -> Order:
        order = await self.orders.get_scoped(order_id, merchant_id)
        if not order:
            raise OrderNotFoundError()
        old_status = order.order_status
        updated = await self.orders.update_status(order, new_status)
        if new_status != old_status:
            customer_msg = _customer_status_message(updated, new_status)
            if customer_msg:
                await self._notify_customer(updated, customer_msg)
        return updated

    async def attach_payment_proof(
        self,
        *,
        merchant_id: UUID,
        telegram_user_id: int | None,
        order_id: UUID,
        file_bytes: bytes,
        filename: str,
        is_dev: bool = False,
    ) -> Order:
        """Mini App receipt upload. Scopes to the placing customer (unless dev)."""
        order = await self.orders.get_scoped(order_id, merchant_id)
        if not order:
            raise OrderNotFoundError()
        info = order.customer_info or {}
        placed_by = info.get("telegram_user_id")
        if (
            not is_dev
            and telegram_user_id is not None
            and placed_by is not None
            and placed_by != telegram_user_id
        ):
            raise OrderNotFoundError()  # treat as not-owned to avoid leaking existence

        object_key = ReceiptStorage().upload(
            merchant_id=merchant_id,
            order_id=order_id,
            data=file_bytes,
            filename=filename,
        )
        now = datetime.now(timezone.utc)
        order.payment_proof_url = object_key
        order.payment_proof_uploaded_at = now
        order.payment_rejection_reason = None
        order.order_status = OrderStatus.PAYMENT_SUBMITTED
        await self.db.flush()
        await self.db.refresh(order)

        await self._publish_alert(
            merchant_id,
            "PAYMENT_SUBMITTED",
            {
                "order_id": str(order.id),
                "total": str(order.total_amount),
                "customer_name": (info or {}).get("name") or "Customer",
            },
        )
        return order

    async def verify_payment(
        self, *, merchant_id: UUID, order_id: UUID, admin_user_id: UUID
    ) -> Order:
        order = await self.orders.get_scoped(order_id, merchant_id)
        if not order:
            raise OrderNotFoundError()
        order.order_status = OrderStatus.PAYMENT_VERIFIED
        order.payment_verified_at = datetime.now(timezone.utc)
        order.payment_verified_by = admin_user_id
        order.payment_rejection_reason = None
        await self.db.flush()
        await self.db.refresh(order)
        await self._publish_alert(
            merchant_id,
            "PAYMENT_VERIFIED",
            {"order_id": str(order.id)},
        )
        await self._notify_customer(
            order,
            f"✅ *Payment verified!* Your order #{str(order.id)[:8]} for ETB {order.total_amount} is being prepared. "
            "We'll message you here when it ships.",
        )
        return order

    async def reject_payment(
        self, *, merchant_id: UUID, order_id: UUID, reason: str
    ) -> Order:
        order = await self.orders.get_scoped(order_id, merchant_id)
        if not order:
            raise OrderNotFoundError()
        order.order_status = OrderStatus.PAYMENT_REJECTED
        order.payment_rejection_reason = reason
        await self.db.flush()
        await self.db.refresh(order)
        await self._publish_alert(
            merchant_id,
            "PAYMENT_REJECTED",
            {"order_id": str(order.id), "reason": reason},
        )
        await self._notify_customer(
            order,
            f"❌ *Receipt rejected* for order #{str(order.id)[:8]}.\n"
            f"Reason: _{reason}_\n\n"
            "Please reply with a clearer screenshot of your payment.",
        )
        return order

    async def create_from_channel_comment(
        self,
        *,
        merchant_id: UUID,
        product_id: UUID,
        telegram_user_id: int,
        customer_name: str | None,
        receipt_bytes: bytes,
        receipt_filename: str,
    ) -> Order:
        """Draft order created when a customer posts a payment screenshot in a
        product's discussion-group thread. The customer has already paid, so
        we do NOT block on stock — admin will reconcile if we're short. We
        reserve when we can; if we can't, the order is still created and the
        notes flag it for manual handling."""
        product = await self.products.get(product_id, merchant_id)
        if not product:
            raise ProductMissingError(str(product_id))

        ledger = await self.inventory.get_for_update(product_id)
        stock_warning: str | None = None
        if ledger:
            available = ledger.quantity - ledger.reserved_quantity
            if available >= 1:
                ledger.reserved_quantity += 1
            else:
                stock_warning = (
                    f"Stock unavailable at the time of payment "
                    f"(quantity={ledger.quantity}, reserved={ledger.reserved_quantity}). "
                    "Please reconcile with the customer."
                )
        else:
            stock_warning = "No inventory record for this product. Please reconcile with the customer."

        unit_price = product.base_price or Decimal("0")
        total = Decimal(str(unit_price))

        payment_account = await self.payments.get_default(merchant_id)
        payment_account_id = payment_account.id if payment_account else None

        notes_parts = [
            "Auto-created from a payment screenshot posted in the channel discussion group. Quantity assumed 1 — please confirm with the customer.",
        ]
        if stock_warning:
            notes_parts.append(stock_warning)
        order = await self.orders.create_with_items(
            merchant_id=merchant_id,
            channel_source=ChannelSource.TELEGRAM,
            customer_info={
                "name": customer_name,
                "telegram_user_id": telegram_user_id,
                "source": "channel_comment",
            },
            notes="\n\n".join(notes_parts),
            total_amount=total,
            order_status=OrderStatus.PAYMENT_SUBMITTED,
            payment_account_id=payment_account_id,
            items=[
                {
                    "product_id": product_id,
                    "quantity": 1,
                    "unit_price": unit_price,
                }
            ],
        )

        object_key = ReceiptStorage().upload(
            merchant_id=merchant_id,
            order_id=order.id,
            data=receipt_bytes,
            filename=receipt_filename,
        )
        now = datetime.now(timezone.utc)
        order.payment_proof_url = object_key
        order.payment_proof_uploaded_at = now
        await self.db.flush()
        await self.db.refresh(order)

        await self._publish_alert(
            merchant_id,
            "PAYMENT_SUBMITTED",
            {
                "order_id": str(order.id),
                "total": str(total),
                "customer_name": customer_name or "Customer",
                "source": "channel_comment",
            },
        )
        return order

    async def _publish_alert(self, merchant_id: UUID, type_: str, payload: dict) -> None:
        redis = await get_redis()
        body = json.dumps({"type": type_, "payload": payload})
        await redis.publish(f"ws:alerts:{merchant_id}", body)

    async def _notify_customer(self, order: Order, message: str) -> None:
        """DM the customer via the merchant's Telegram bot. Best-effort: any
        failure (bot not running, user blocked the bot, etc.) is logged and
        swallowed — we never want a notification failure to roll back the
        underlying status change."""
        info = order.customer_info or {}
        tg_user_id = info.get("telegram_user_id")
        if not tg_user_id:
            return
        url = f"{settings.TELEGRAM_SERVICE_URL}/api/v1/telegram/internal/dm-customer"
        body = {
            "merchant_id": str(order.merchant_id),
            "telegram_user_id": int(tg_user_id),
            "message": message,
        }
        headers = {"X-Service-Token": settings.X_SERVICE_TOKEN}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=body)
                if resp.status_code >= 400:
                    logger.warning(
                        "customer_dm_failed",
                        order_id=str(order.id),
                        status_code=resp.status_code,
                        body=resp.text[:200],
                    )
        except Exception as exc:
            logger.warning(
                "customer_dm_exception",
                order_id=str(order.id),
                error=str(exc),
            )
