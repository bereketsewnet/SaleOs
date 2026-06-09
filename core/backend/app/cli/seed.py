"""
Idempotent dev seed. Run via:
    docker exec saleos-core python -m app.cli.seed
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.merchant import Merchant
from app.models.telegram import TelegramBotConfig, TelegramDMContact
from app.models.user import User, UserRole


SUPER_ADMIN = {
    "email": "super@saleos.com",
    "password": "super1234",
    "first_name": "Platform",
    "last_name": "Owner",
    "phone_number": "+251900000000",
    "role": UserRole.SUPER_ADMIN,
}

MERCHANTS = [
    {
        "merchant": {
            "business_name": "Habesha Coffee",
            "contact_phone": "+251911111111",
            "contact_email": "contact@habesha.com",
        },
        "users": [
            {
                "email": "admin@habesha.com",
                "password": "admin1234",
                "first_name": "Abebe",
                "last_name": "Bekele",
                "phone_number": "+251911111112",
                "role": UserRole.ADMIN,
            },
            {
                "email": "manager@habesha.com",
                "password": "manager1234",
                "first_name": "Tigist",
                "last_name": "Kebede",
                "phone_number": "+251911111113",
                "role": UserRole.MANAGER,
            },
            {
                "email": "staff@habesha.com",
                "password": "staff1234",
                "first_name": "Yonas",
                "last_name": "Alemu",
                "phone_number": "+251911111114",
                "role": UserRole.STAFF,
            },
            {
                "email": "customer@habesha.com",
                "password": "customer1234",
                "first_name": "Sara",
                "last_name": "Mengistu",
                "phone_number": "+251911111115",
                "role": UserRole.CUSTOMER,
            },
        ],
    },
    {
        "merchant": {
            "business_name": "Buna Roasters",
            "contact_phone": "+251922222222",
            "contact_email": "contact@buna.com",
        },
        "users": [
            {
                "email": "admin@buna.com",
                "password": "admin1234",
                "first_name": "Daniel",
                "last_name": "Tesfaye",
                "phone_number": "+251922222223",
                "role": UserRole.ADMIN,
            },
        ],
    },
]


async def _get_or_create_merchant(db, payload: dict) -> Merchant:
    result = await db.execute(
        select(Merchant).where(Merchant.contact_email == payload["contact_email"])
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    merchant = Merchant(**payload)
    db.add(merchant)
    await db.flush()
    return merchant


async def _get_or_create_user(db, *, merchant_id, user_data: dict) -> tuple[User, bool]:
    result = await db.execute(select(User).where(User.email == user_data["email"]))
    existing = result.scalar_one_or_none()
    if existing:
        return existing, False
    user = User(
        email=user_data["email"],
        password_hash=hash_password(user_data["password"]),
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        phone_number=user_data["phone_number"],
        role=user_data["role"],
        is_verified=True,
        merchant_id=merchant_id,
    )
    db.add(user)
    await db.flush()
    return user, True


HABESHA_EMAIL = "contact@habesha.com"

HABESHA_DEFAULT_IDENTIFIER = (
    "We sell quality footwear and apparel — original brands. Most items are in "
    "stock in sizes 38–46 (shoes) and S/M/L/XL (clothes). Colors vary by item; "
    "tell the customer to check the product page for exact colors. We're based "
    "in Addis Ababa. Replies can be in Amharic, English, or mixed."
)

HABESHA_DEFAULT_INSTRUCTIONS = (
    "ALWAYS share the product price when the customer asks — we sell openly.\n"
    "ALWAYS share OUR contact info and OUR bank accounts with the customer when "
    "they want to buy. NEVER ask the customer to share THEIR phone, email, or "
    "contact info — we do not need it.\n"
    "When the customer says they want to BUY / PAY / ORDER, reply with: "
    "(1) the product's price, (2) ALL of OUR active bank accounts with bank name "
    "+ account number + holder name, (3) the first PHONE and first TELEGRAM_USERNAME "
    "from OUR contact list. Tell the customer to send the payment screenshot to "
    "that phone or Telegram username.\n"
    "When the customer asks for SUPPORT or more details: share the product "
    "description, identifier, and OUR first phone + first Telegram username so "
    "they can reach us directly.\n"
    "If the customer asks about other products, suggest 1-3 from the catalog "
    "and share their deep links.\n"
    "FORBIDDEN: 'please share your contact', 'provide your phone', "
    "'a consultant will reach out'."
)

HABESHA_DM_CONTACTS = [
    {"kind": "TELEGRAM_USERNAME", "value": "@habesha_owner", "label": "Owner",   "position": 0},
    {"kind": "TELEGRAM_USERNAME", "value": "@habesha_help",  "label": "Support", "position": 1},
    {"kind": "PHONE",             "value": "+251911111112",   "label": "Owner",   "position": 0},
    {"kind": "PHONE",             "value": "+251911111113",   "label": "Support", "position": 1},
    {"kind": "EMAIL",             "value": "orders@habesha.com", "label": "Orders", "position": 0},
    {"kind": "ADDRESS",           "value": "Bole, Addis Ababa, Ethiopia", "label": "Shop", "position": 0},
]


async def _seed_habesha_extras(db, habesha_merchant_id, force_defaults: bool = False) -> tuple[bool, int]:
    """Set Habesha's default product context + DM contacts.
    Returns (bot_config_updated, dm_contacts_inserted).
    If force_defaults=True, overwrites existing identifier + instructions."""
    bot_cfg_updated = False
    cfg_result = await db.execute(
        select(TelegramBotConfig).where(TelegramBotConfig.merchant_id == habesha_merchant_id)
    )
    cfg = cfg_result.scalar_one_or_none()
    if cfg:
        if force_defaults or not cfg.default_product_identifier:
            cfg.default_product_identifier = HABESHA_DEFAULT_IDENTIFIER
            bot_cfg_updated = True
        if force_defaults or not cfg.default_product_instructions:
            cfg.default_product_instructions = HABESHA_DEFAULT_INSTRUCTIONS
            bot_cfg_updated = True
        if bot_cfg_updated:
            await db.flush()

    inserted = 0
    for c in HABESHA_DM_CONTACTS:
        existing = (await db.execute(
            select(TelegramDMContact).where(
                TelegramDMContact.merchant_id == habesha_merchant_id,
                TelegramDMContact.kind == c["kind"],
                TelegramDMContact.value == c["value"],
            )
        )).scalar_one_or_none()
        if existing:
            continue
        db.add(TelegramDMContact(
            merchant_id=habesha_merchant_id,
            kind=c["kind"],
            value=c["value"],
            label=c.get("label"),
            position=c["position"],
            is_active=True,
        ))
        inserted += 1
    if inserted:
        await db.flush()
    return bot_cfg_updated, inserted


async def seed(force_defaults: bool = False) -> None:
    created_users = 0
    created_merchants = 0
    skipped_users = 0

    async with AsyncSessionLocal() as db:
        # Super admin (no merchant)
        _, was_new = await _get_or_create_user(db, merchant_id=None, user_data=SUPER_ADMIN)
        if was_new:
            created_users += 1
        else:
            skipped_users += 1

        habesha_merchant_id = None

        # Per-merchant seeds
        for spec in MERCHANTS:
            merchant_before = (await db.execute(
                select(Merchant).where(Merchant.contact_email == spec["merchant"]["contact_email"])
            )).scalar_one_or_none()
            merchant = await _get_or_create_merchant(db, spec["merchant"])
            if merchant_before is None:
                created_merchants += 1
            if merchant.contact_email == HABESHA_EMAIL:
                habesha_merchant_id = merchant.id

            for user_data in spec["users"]:
                _, was_new = await _get_or_create_user(
                    db, merchant_id=merchant.id, user_data=user_data
                )
                if was_new:
                    created_users += 1
                else:
                    skipped_users += 1

        # Habesha-specific extras (defaults + DM contacts). Idempotent.
        bot_cfg_updated = False
        contacts_inserted = 0
        if habesha_merchant_id:
            bot_cfg_updated, contacts_inserted = await _seed_habesha_extras(
                db, habesha_merchant_id, force_defaults=force_defaults
            )

        await db.commit()

    print(
        f"Seed complete. Merchants created: {created_merchants}. "
        f"Users created: {created_users}. Users already present: {skipped_users}. "
        f"Habesha bot defaults applied: {bot_cfg_updated}. "
        f"Habesha DM contacts inserted: {contacts_inserted}."
    )


if __name__ == "__main__":
    import sys

    force = "--force-defaults" in sys.argv
    asyncio.run(seed(force_defaults=force))
