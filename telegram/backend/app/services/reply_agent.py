"""Reply agent. Composes a system prompt from the merchant's brand voice + default
product context + per-product overrides + DM contacts, and asks the configured
provider to write a reply for either a DM or a channel-comment surface."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal
from uuid import UUID

import structlog

from app.bot.context import BotMerchantContext
from app.services.ai_provider import AIError, complete_text

logger = structlog.get_logger()


Surface = Literal["DM", "COMMENT"]


@dataclass(frozen=True)
class ProductContext:
    product_id: UUID
    merchant_id: UUID
    title: str
    description: str | None
    base_price: Decimal | None
    image_urls: list[str]
    identifier_effective: str | None
    instructions_effective: str | None
    is_ocr_identified: bool


_GREETING_BY_LANG: dict[str, str] = {
    "AMHARIC": "ሰላም! ምን ልርዳዎት?",
    "ENGLISH": "Hi! How can I help?",
}


def _fallback_greeting(lang: str | None) -> str:
    if lang and lang.upper() in _GREETING_BY_LANG:
        return _GREETING_BY_LANG[lang.upper()]
    return f"{_GREETING_BY_LANG['AMHARIC']}\n{_GREETING_BY_LANG['ENGLISH']}"


def _format_payment_accounts(accounts: list[dict]) -> str:
    if not accounts:
        return "(none on file — do NOT invent banks or accounts)"
    lines: list[str] = []
    for idx, a in enumerate(accounts, 1):
        bank = a.get("bank_name") or ""
        acct_no = a.get("account_number") or ""
        holder = a.get("account_holder_name") or ""
        phone = a.get("phone") or ""
        line = f"  {idx}. {bank} — Account: {acct_no} — Name: {holder}"
        if phone:
            line += f" — Phone: {phone}"
        lines.append(line)
    return "\n".join(lines)


def _format_dm_contacts(contacts: list[dict]) -> str:
    if not contacts:
        return "(none on file — do NOT invent contacts)"
    grouped: dict[str, list[dict]] = {}
    for c in contacts:
        grouped.setdefault(c["kind"], []).append(c)
    lines: list[str] = []
    nice = {
        "TELEGRAM_USERNAME": "Telegram usernames",
        "PHONE": "Phone numbers",
        "EMAIL": "Emails",
        "ADDRESS": "Addresses",
        "OTHER": "Other info",
    }
    for kind, items in grouped.items():
        items.sort(key=lambda x: x.get("position", 0))
        lines.append(f"{nice.get(kind, kind)}:")
        for i, item in enumerate(items, 1):
            label = f" ({item['label']})" if item.get("label") else ""
            lines.append(f"  {i}. {item['value']}{label}")
    return "\n".join(lines)


def _format_catalog(catalog: list[dict], bot_username: str | None, exclude_id: str | None) -> str:
    if not catalog:
        return "(empty)"
    lines: list[str] = []
    for p in catalog:
        if exclude_id and p["id"] == exclude_id:
            continue
        title = p.get("title", "")
        price = p.get("base_price")
        price_txt = f"ETB {price}" if price else "(no price set)"
        identifier = (p.get("identifier_effective") or "").strip()
        if identifier:
            identifier = identifier[:140] + ("…" if len(identifier) > 140 else "")
        deep_link = (
            f"https://t.me/{bot_username}?start=product_{p['id']}"
            if bot_username
            else f"(product id: {p['id']})"
        )
        lines.append(f"- {title} · {price_txt}")
        if identifier:
            lines.append(f"  About: {identifier}")
        lines.append(f"  Link: {deep_link}")
    return "\n".join(lines) if lines else "(empty)"


def _build_system_prompt(
    merchant: BotMerchantContext,
    product_ctx: ProductContext | None,
    surface: Surface,
    catalog: list[dict] | None = None,
) -> str:
    parts: list[str] = []

    # 1. Brand identity
    parts.append("=== BRAND ===")
    if merchant.business_name:
        parts.append(f"Business: {merchant.business_name}")
    if merchant.business_type:
        parts.append(f"Type: {merchant.business_type}")
    if merchant.business_description:
        parts.append(f"About: {merchant.business_description}")
    if merchant.system_prompt:
        parts.append(f"Tone rules:\n{merchant.system_prompt}")

    # 2. Default product context (the agent falls back here when product is unknown)
    parts.append("\n=== DEFAULT PRODUCT CONTEXT ===")
    parts.append(
        f"Default identifier: {merchant.default_product_identifier or '(none set)'}"
    )
    parts.append(
        f"Default instructions: {merchant.default_product_instructions or '(none set)'}"
    )

    # 3. Per-product overrides (effective values already resolved by Core)
    if product_ctx is not None:
        parts.append("\n=== THIS PRODUCT ===")
        parts.append(f"Title: {product_ctx.title}")
        if product_ctx.description:
            parts.append(f"Description: {product_ctx.description}")
        if product_ctx.base_price is not None:
            parts.append(f"Price: ETB {product_ctx.base_price}")
        parts.append(
            f"Identifier (private): {product_ctx.identifier_effective or '(none)'}"
        )
        parts.append(
            f"Instructions (must follow strictly):\n"
            f"{product_ctx.instructions_effective or '(none — follow default instructions above)'}"
        )

    # 4. OUR contact info (to be shared with customers when they want to reach us)
    parts.append("\n=== OUR CONTACT INFO (share with customers when they want to reach us) ===")
    parts.append(
        "These are OUR phones, OUR Telegram usernames, OUR emails, OUR address. "
        "Share them WITH the customer when relevant — never ask the customer for theirs."
    )
    parts.append(_format_dm_contacts(merchant.dm_contacts))

    # 4b. OUR payment accounts (bank info for customers to pay us)
    parts.append("\n=== OUR PAYMENT ACCOUNTS (share when the customer wants to pay) ===")
    parts.append(
        "These are OUR bank accounts. When the customer says they want to buy / pay / order, "
        "share at least one of these in full along with at least one phone/Telegram username "
        "above so they can confirm the order."
    )
    parts.append(_format_payment_accounts(merchant.payment_accounts))

    # 5. Full catalog (so the agent can suggest other products with deep links)
    parts.append("\n=== CATALOG (other products you can suggest) ===")
    parts.append(
        "If the customer asks for other products / alternatives / what else you have, "
        "pick 1–3 from this list and share the Link so they can deep-link to that product "
        "(opens this bot in a DM with that product already in context)."
    )
    parts.append(
        _format_catalog(
            catalog or [],
            merchant.bot_username,
            exclude_id=str(product_ctx.product_id) if product_ctx else None,
        )
    )

    # 5. Hard rules
    lang = merchant.language_preference or "AUTO"
    if lang == "AUTO":
        lang_rule = "Match the language the customer used (Amharic or English; mixed is fine)."
    elif lang == "AMHARIC":
        lang_rule = "Always reply in Amharic."
    else:
        lang_rule = "Always reply in English."

    surface_rule = (
        "This is a PUBLIC comment under a channel post — keep replies short, friendly, and respect any 'do not reveal X' instruction."
        if surface == "COMMENT"
        else "This is a private direct message."
    )

    parts.append("\n=== HARD RULES (highest priority — override everything else) ===")
    parts.append(f"- {lang_rule}")
    parts.append(f"- {surface_rule}")
    parts.append(
        "- The phones, Telegram usernames, emails, address, and bank accounts in this prompt are OURS — the business owner's. "
        "Your job is to SHARE these WITH the customer. NEVER ask the customer to share their own phone, email, address, or contact details — we don't need them. "
        "Forbidden phrases include: 'share your contact', 'provide your phone', 'send us your email', 'a consultant will reach out'."
    )
    parts.append(
        "- When the customer says they want to BUY / PAY / ORDER / interested in purchasing → reply with:\n"
        "    1) the product's price (unless per-product instructions say otherwise),\n"
        "    2) at least one of OUR PAYMENT ACCOUNTS (bank name + account number + holder name) in full,\n"
        "    3) at least one of OUR CONTACT entries — typically the first PHONE and/or first TELEGRAM_USERNAME — so they confirm with us after paying.\n"
        "  Tell them to send the payment screenshot to that contact."
    )
    parts.append(
        "- When the customer asks for SUPPORT or general help → share OUR first PHONE + first TELEGRAM_USERNAME."
    )
    parts.append("- Follow per-product instructions LITERALLY when they exist, even if it conflicts with default behavior.")
    parts.append("- NEVER invent products, prices, addresses, phone numbers, emails, usernames, or bank accounts that aren't in this prompt.")
    parts.append("- When an instruction says 'share the first phone' or 'send my Telegram', use the FIRST entry under that kind above.")
    parts.append("- Keep replies short (1–3 sentences for comments, up to 8 for DM with bank details).")

    return "\n".join(parts)


async def generate_reply(
    *,
    merchant: BotMerchantContext,
    customer_message: str,
    product_ctx: ProductContext | None,
    surface: Surface,
    catalog: list[dict] | None = None,
) -> str:
    if not merchant.ai_provider or not merchant.ai_api_key:
        return _fallback_greeting(merchant.language_preference)

    system_prompt = _build_system_prompt(merchant, product_ctx, surface, catalog)
    user_prompt = (
        f"Customer message:\n{customer_message.strip()}\n\n"
        "Write the reply now."
    )

    try:
        text = await complete_text(
            provider=merchant.ai_provider,
            api_key=merchant.ai_api_key,
            model=merchant.ai_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=600 if surface == "DM" else 250,
        )
        text = text.strip()
        return text or _fallback_greeting(merchant.language_preference)
    except AIError as exc:
        logger.warning(
            "reply_agent_failed",
            merchant_id=str(merchant.merchant_id),
            surface=surface,
            error=str(exc),
        )
        return _fallback_greeting(merchant.language_preference)
