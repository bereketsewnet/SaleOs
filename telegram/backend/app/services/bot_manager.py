import asyncio
from uuid import UUID

import structlog
from aiogram import Bot, Dispatcher

from app.bot.context import BotMerchantContext
from app.bot.dispatcher import build_bot, build_dispatcher, shutdown_bot
from app.core.redis import get_redis
from app.services.core_client import CoreClient

logger = structlog.get_logger()


class _ManagedBot:
    def __init__(self, bot: Bot, dispatcher: Dispatcher, task: asyncio.Task) -> None:
        self.bot = bot
        self.dispatcher = dispatcher
        self.task = task


class BotManager:
    """
    Manages one aiogram Bot + Dispatcher + polling task per merchant.
    Single asyncio event loop hosts all bots.
    """

    def __init__(self) -> None:
        self._bots: dict[UUID, _ManagedBot] = {}
        self._lock = asyncio.Lock()
        self._core = CoreClient()

    def get_bot_for_merchant(self, merchant_id: UUID) -> "_ManagedBot | None":
        return self._bots.get(merchant_id)

    async def start_all(self) -> None:
        try:
            configs = await self._core.list_telegram_configs()
        except Exception as exc:
            logger.warning("bot_manager_initial_fetch_failed", error=str(exc))
            return
        for cfg in configs:
            await self._start_one(cfg)

    async def reload(self, merchant_id: UUID) -> bool:
        """Reload (or remove) a single merchant's bot."""
        await self.stop_one(merchant_id)
        try:
            cfg = await self._core.get_telegram_config(merchant_id)
        except Exception as exc:
            logger.warning("bot_manager_reload_fetch_failed", merchant_id=str(merchant_id), error=str(exc))
            return False
        if not cfg:
            return False
        await self._start_one(cfg)
        return True

    async def stop_one(self, merchant_id: UUID) -> None:
        async with self._lock:
            managed = self._bots.pop(merchant_id, None)
        if managed is None:
            return
        managed.task.cancel()
        try:
            await managed.task
        except (asyncio.CancelledError, Exception):
            pass
        await shutdown_bot(managed.bot)
        logger.info("bot_manager_stopped", merchant_id=str(merchant_id))

    async def stop_all(self) -> None:
        async with self._lock:
            ids = list(self._bots.keys())
        for mid in ids:
            await self.stop_one(mid)

    async def _start_one(self, cfg: dict) -> None:
        merchant_id = UUID(cfg["merchant_id"])
        if not cfg.get("is_active"):
            return
        bot = build_bot(cfg["bot_token"])
        merchant = BotMerchantContext(
            merchant_id=merchant_id,
            bot_username=cfg.get("bot_username"),
            welcome_message=cfg.get("welcome_message"),
            language_preference=cfg.get("language_preference") or "AUTO",
            business_name=cfg.get("business_name"),
            business_type=cfg.get("business_type"),
            business_description=cfg.get("business_description"),
            system_prompt=cfg.get("system_prompt"),
            ai_provider=cfg.get("ai_provider"),
            ai_api_key=cfg.get("ai_api_key"),
            ai_model=cfg.get("ai_model"),
            ai_auto_reply_dm=cfg.get("ai_auto_reply_dm", False),
            ai_auto_reply_comments=cfg.get("ai_auto_reply_comments", False),
            ai_parse_hashtag_products=cfg.get("ai_parse_hashtag_products", True),
            channel_id=cfg.get("channel_id"),
            default_product_identifier=cfg.get("default_product_identifier"),
            default_product_instructions=cfg.get("default_product_instructions"),
            dm_contacts=cfg.get("dm_contacts") or [],
            payment_accounts=cfg.get("payment_accounts") or [],
        )
        redis = await get_redis()
        from aiogram.fsm.storage.redis import RedisStorage
        storage = RedisStorage(redis=redis)
        dp = build_dispatcher(storage, merchant)

        async def _poll() -> None:
            backoff = 2.0
            while True:
                try:
                    await dp.start_polling(bot, handle_signals=False)
                    # start_polling normally only returns when stopped — break out.
                    return
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.error(
                        "bot_polling_crashed",
                        merchant_id=str(merchant_id),
                        error=str(exc),
                        retry_in=backoff,
                    )
                    try:
                        await asyncio.sleep(backoff)
                    except asyncio.CancelledError:
                        raise
                    backoff = min(backoff * 2, 60.0)

        task = asyncio.create_task(_poll(), name=f"bot-poll-{merchant_id}")
        async with self._lock:
            self._bots[merchant_id] = _ManagedBot(bot=bot, dispatcher=dp, task=task)
        logger.info(
            "bot_manager_started",
            merchant_id=str(merchant_id),
            bot_username=cfg.get("bot_username"),
        )


_manager: BotManager | None = None


def get_bot_manager() -> BotManager:
    global _manager
    if _manager is None:
        _manager = BotManager()
    return _manager
