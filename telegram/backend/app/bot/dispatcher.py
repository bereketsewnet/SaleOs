from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from app.bot.context import BotMerchantContext
from app.bot.handlers import channel as channel_handler
from app.bot.handlers import discussion_group as discussion_group_handler
from app.bot.handlers import dm as dm_handler
from app.bot.handlers import start as start_handler


def build_bot(token: str) -> Bot:
    return Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_dispatcher(storage: RedisStorage, merchant: BotMerchantContext) -> Dispatcher:
    """Per-merchant dispatcher. Builds a FRESH Router per call so reloads work."""
    dp = Dispatcher(storage=storage)
    dp["merchant"] = merchant

    root_router = Router(name=f"merchant-{merchant.merchant_id}")
    # Order matters: command /start first, then channel + group + DM catch-all.
    start_handler.register(root_router)
    channel_handler.register(root_router)
    discussion_group_handler.register(root_router)
    dm_handler.register(root_router)
    dp.include_router(root_router)
    return dp


async def shutdown_bot(bot: Bot) -> None:
    try:
        await bot.session.close()
    except Exception:
        pass
