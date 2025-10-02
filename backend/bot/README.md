# Telegram Bot для Clicker Game

## Настройка

1. **Создайте файл .env в этой папке** на основе `config_example.txt`:
   ```bash
   cp config_example.txt .env
   ```

2. **Заполните .env файл своими данными:**
   ```env
   BOT_TOKEN=your_actual_bot_token_from_botfather
   WEBAPP_URL=https://your-deployed-domain.com
   JWT_SECRET=optional_custom_secret
   ```

3. **Установите зависимости** (если еще не установлены):
   ```bash
   # Активируйте виртуальное окружение
   venv/Scripts/activate  # Windows
   # или
   source venv/bin/activate  # Linux/Mac
   
   # Установите зависимости
   pip install aiogram python-dotenv
   ```

## Запуск

### Способ 1: Из папки bot
```bash
cd backend/bot
python bot.py
```

### Способ 2: Используя скрипт запуска
```bash
# Из корня проекта
python backend/run_bot.py
```

## Структура

- `bot.py` - основной файл бота
- `venv/` - виртуальное окружение с зависимостями
- `.env` - конфигурационный файл (создайте сами)
- `config_example.txt` - пример конфигурации

## Возможности бота

- `/start` - приветствие и кнопка для открытия веб-приложения
- `/balance` - показать баланс пользователя и кнопку для игры

Весь геймплей происходит в веб-приложении, бот служит только для входа и базовой информации.
