import os
import asyncio
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from dotenv import load_dotenv, find_dotenv
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db.database import DatabaseManager


# Load .env from current dir (bot folder) or project root
env_path = Path(__file__).parent / '.env'
_ = load_dotenv(env_path) or load_dotenv(find_dotenv(usecwd=True))

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")  # e.g. https://your-domain.example

# Инициализируем базу данных
db_manager = DatabaseManager()


if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Export BOT_TOKEN env var with your bot token from @BotFather.")

if not WEBAPP_URL:
    # Not critical for start, but warn
    print("[WARN] WEBAPP_URL is not set. Set WEBAPP_URL to your deployed site to enable the WebApp button.")


async def on_start_command(message: Message):
    # Инициализируем пользователя в системе
    telegram_data = {
        "username": message.from_user.username or "",
        "first_name": message.from_user.first_name or "",
        "last_name": message.from_user.last_name or ""
    }
    db_manager.create_or_update_user(message.from_user.id, telegram_data)
    
    # Обработка реферальных ссылок
    command_args = message.text.split(' ', 1)
    if len(command_args) > 1 and command_args[1].startswith('ref_'):
        try:
            referrer_id = int(command_args[1].replace('ref_', ''))
            db_manager.add_referral(referrer_id, message.from_user.id)
        except ValueError:
            pass  # Игнорируем неверные реферальные коды
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Открыть игру",
                    web_app=WebAppInfo(url=WEBAPP_URL) if WEBAPP_URL else None,
                )
            ]
        ]
    )

    text = (
        "🍖 <b>Добро пожаловать в Shaurmafia!</b>\n\n"
        "🎮 Кликай по шаурме, зарабатывай монеты и покупай улучшения!\n"
        "💰 Покупка монет и весь геймплей доступны в приложении\n\n"
        "Нажми кнопку ниже, чтобы начать играть!"
    )

    if not WEBAPP_URL:
        text += f"\n\n⚠️ <i>WEBAPP_URL не настроен</i>"

    await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)




async def show_balance(message: Message):
    """Показать баланс пользователя"""
    user_info = db_manager.get_user_profile(message.from_user.id)
    
    balance_text = (
        f"💰 <b>Ваш баланс</b>\n\n"
        f"💎 Монеты: <b>{user_info['coins']}</b>\n"
        f"🔥 Сила клика: <b>{user_info['click_power']}</b>\n"
        f"⚡ Пассивный доход: <b>{user_info['passive_income']}/сек</b>\n"
        f"🛒 Всего покупок: <b>{user_info['total_purchases']}</b>\n"
        f"👥 Рефералов: <b>{user_info['referrals_count']}</b>\n\n"
        f"🎮 Открой игру для покупки монет и улучшений!"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Открыть игру",
                    web_app=WebAppInfo(url=WEBAPP_URL) if WEBAPP_URL else None
                )
            ]
        ]
    )
    
    await message.answer(balance_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def main() -> None:
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Регистрируем обработчики сообщений
    dp.message.register(on_start_command, F.text == "/start")
    dp.message.register(show_balance, F.text == "/balance")

    print("🤖 Bot is starting…")
    print(f"🌐 WebApp URL: {WEBAPP_URL or '❌ Not set'}")
    print("💡 Покупка монет и весь геймплей доступны в веб-приложении")
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass


