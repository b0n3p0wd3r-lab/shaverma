import os
import asyncio
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo,
    LabeledPrice, PreCheckoutQuery, SuccessfulPayment, CallbackQuery
)
from dotenv import load_dotenv, find_dotenv
from user_data import user_manager


# Load .env from current dir or project root
_ = load_dotenv(find_dotenv(usecwd=True)) or load_dotenv(dotenv_path=Path(__file__).with_name('.env'))

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")  # e.g. https://your-domain.example
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")  # Токен от платежного провайдера

# Варианты покупки монет (сумма в рублях, количество монет)
COIN_PACKAGES = [
    {"price": 50, "coins": 100, "title": "Стартовый пакет"},
    {"price": 100, "coins": 250, "title": "Базовый пакет"},
    {"price": 250, "coins": 650, "title": "Популярный пакет"},
    {"price": 500, "coins": 1400, "title": "Выгодный пакет"},
    {"price": 1000, "coins": 3000, "title": "Премиум пакет"},
    {"price": 2000, "coins": 6500, "title": "VIP пакет"}
]


if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Export BOT_TOKEN env var with your bot token from @BotFather.")

if not WEBAPP_URL:
    # Not critical for start, but warn
    print("[WARN] WEBAPP_URL is not set. Set WEBAPP_URL to your deployed site to enable the WebApp button.")


async def on_start_command(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Начать игру",
                    web_app=WebAppInfo(url=WEBAPP_URL) if WEBAPP_URL else None,
                    url=WEBAPP_URL if not WEBAPP_URL else None,
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Купить монеты",
                    callback_data="buy_coins"
                )
            ]
        ]
    )

    text = (
        "🍖 <b>Добро пожаловать в Shaurmafia!</b>\n\n"
        "🎮 Нажми кнопку ниже, чтобы открыть игру\n"
        "💰 Или купи монеты для игры\n\n"
        "Если кнопка не работает, открой: " + (WEBAPP_URL or "<не задан WEBAPP_URL>")
    )

    await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def show_coin_packages(callback: CallbackQuery):
    """Показать варианты покупки монет"""
    keyboard_rows = []
    
    # Создаем кнопки для каждого пакета (по 2 в ряду)
    for i in range(0, len(COIN_PACKAGES), 2):
        row = []
        for j in range(2):
            if i + j < len(COIN_PACKAGES):
                package = COIN_PACKAGES[i + j]
                row.append(InlineKeyboardButton(
                    text=f"💎 {package['coins']} монет - {package['price']}₽",
                    callback_data=f"buy_{i + j}"
                ))
        keyboard_rows.append(row)
    
    # Добавляем кнопку "Назад"
    keyboard_rows.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    text = (
        "💰 <b>Выберите пакет монет:</b>\n\n"
        "💎 Монеты можно потратить на улучшения в игре\n"
        "🎁 Чем больше пакет - тем выгоднее цена!\n\n"
        "Выберите подходящий вариант:"
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def process_coin_purchase(callback: CallbackQuery):
    """Обработка покупки конкретного пакета монет"""
    package_index = int(callback.data.split("_")[1])
    package = COIN_PACKAGES[package_index]
    
    if not PAYMENT_PROVIDER_TOKEN:
        await callback.answer(
            "❌ Платежи временно недоступны. Обратитесь к администратору.",
            show_alert=True
        )
        return
    
    # Создаем счет на оплату
    prices = [LabeledPrice(label=package["title"], amount=package["price"] * 100)]  # в копейках
    
    await callback.message.answer_invoice(
        title=f"💎 {package['title']}",
        description=f"Покупка {package['coins']} игровых монет за {package['price']}₽",
        payload=f"coins_{package['coins']}_{callback.from_user.id}",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="RUB",
        prices=prices,
        start_parameter="game_coins_purchase",
        photo_url="https://via.placeholder.com/400x300/FFD700/000000?text=💎+Монеты",
        photo_width=400,
        photo_height=300,
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        send_phone_number_to_provider=False,
        send_email_to_provider=False,
        is_flexible=False
    )
    
    await callback.answer()


async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """Предварительная проверка платежа"""
    # Здесь можно добавить дополнительные проверки
    # Например, проверить доступность товара, валидность пользователя и т.д.
    
    payload_parts = pre_checkout_query.invoice_payload.split("_")
    if len(payload_parts) != 3 or payload_parts[0] != "coins":
        await pre_checkout_query.answer(
            ok=False,
            error_message="Ошибка в данных платежа. Попробуйте еще раз."
        )
        return
    
    coins_amount = payload_parts[1]
    user_id = payload_parts[2]
    
    # Проверяем, что пользователь совпадает
    if str(pre_checkout_query.from_user.id) != user_id:
        await pre_checkout_query.answer(
            ok=False,
            error_message="Ошибка авторизации. Попробуйте еще раз."
        )
        return
    
    # Все проверки пройдены
    await pre_checkout_query.answer(ok=True)


async def process_successful_payment(message: Message):
    """Обработка успешного платежа"""
    payment = message.successful_payment
    payload_parts = payment.invoice_payload.split("_")
    
    coins_amount = int(payload_parts[1])
    user_id = int(payload_parts[2])
    
    # Начисляем монеты пользователю
    new_balance = user_manager.add_coins(
        user_id=user_id, 
        amount=coins_amount, 
        transaction_id=payment.telegram_payment_charge_id
    )
    
    success_text = (
        f"✅ <b>Платеж успешно обработан!</b>\n\n"
        f"💎 Вам начислено: <b>{coins_amount} монет</b>\n"
        f"💰 Текущий баланс: <b>{new_balance} монет</b>\n"
        f"💳 Сумма платежа: <b>{payment.total_amount // 100}₽</b>\n"
        f"🆔 ID транзакции: <code>{payment.telegram_payment_charge_id}</code>\n\n"
        f"🎮 Монеты уже доступны в игре!"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Открыть игру",
                    web_app=WebAppInfo(url=WEBAPP_URL) if WEBAPP_URL else None
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Купить еще монет",
                    callback_data="buy_coins"
                )
            ]
        ]
    )
    
    await message.answer(success_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def handle_back_to_start(callback: CallbackQuery):
    """Возврат к стартовому меню"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Начать игру",
                    web_app=WebAppInfo(url=WEBAPP_URL) if WEBAPP_URL else None,
                    url=WEBAPP_URL if not WEBAPP_URL else None,
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Купить монеты",
                    callback_data="buy_coins"
                )
            ]
        ]
    )

    text = (
        "🍖 <b>Добро пожаловать в Shaurmafia!</b>\n\n"
        "🎮 Нажми кнопку ниже, чтобы открыть игру\n"
        "💰 Или купи монеты для игры\n\n"
        "Если кнопка не работает, открой: " + (WEBAPP_URL or "<не задан WEBAPP_URL>")
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


async def show_balance(message: Message):
    """Показать баланс пользователя"""
    user_info = user_manager.get_user_info(message.from_user.id)
    
    balance_text = (
        f"💰 <b>Ваш баланс</b>\n\n"
        f"💎 Монеты: <b>{user_info['coins']}</b>\n"
        f"🛒 Всего покупок: <b>{user_info['total_purchases']}</b>\n\n"
        f"💡 Монеты можно потратить на улучшения в игре!"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Открыть игру",
                    web_app=WebAppInfo(url=WEBAPP_URL) if WEBAPP_URL else None
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Купить монеты",
                    callback_data="buy_coins"
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
    dp.message.register(process_successful_payment, F.successful_payment)
    
    # Регистрируем обработчики callback'ов
    dp.callback_query.register(show_coin_packages, F.data == "buy_coins")
    dp.callback_query.register(handle_back_to_start, F.data == "back_to_start")
    dp.callback_query.register(process_coin_purchase, F.data.startswith("buy_"))
    
    # Регистрируем обработчик предварительной проверки платежа
    dp.pre_checkout_query.register(process_pre_checkout)

    print("🤖 Bot is starting…")
    print(f"💰 Payment provider token: {'✅ Set' if PAYMENT_PROVIDER_TOKEN else '❌ Not set'}")
    print(f"🌐 WebApp URL: {WEBAPP_URL or '❌ Not set'}")
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass


