### Требования и подготовка окружения

- Собственный Linux‑сервер (рекомендуется Ubuntu 22.04/24.04 LTS)
- Доменное имя (любой регистратор: Reg.ru, Namecheap, Cloudflare Registrar и т. п.)
- Публичный статический IP адрес для сервера
- Доступ по SSH и права sudo
- Установленные: `git`, `curl`, `node`/`python` (в зависимости от бэкенда), `nginx`, `certbot` (будет установлен ниже)


-------------------------------------------------------------------------------

### Проверка подписи initData на бэкенде

Telegram Mini App передаёт в WebView строку `initData`. Фронтенд отправляет её на ваш бэкенд. Бэкенд обязан верифицировать HMAC подпись с помощью `BOT_TOKEN`.

Фронтенд отправляет `initData` как `application/x-www-form-urlencoded`:

```javascript
const initData = window.Telegram?.WebApp?.initData;
await fetch('/api/auth/telegram', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: initData,
});
```
-------------------------------------------------------------------------------

### Настройка Mini App в BotFather

В Telegram найдите бота `@BotFather`.

1) Установите домен для Mini App:

/setdomain
<выберите бота>
https://example.com

-------------------------------------------------------------------------------

2) Привяжите WebApp к меню бота или создайте Mini App:

- Вариант A (меню):
/setmenubutton
<выберите бота>
Web App
Название: Clicker
URL: https://example.com

- Вариант B (Mini App): `/newapp` (если доступно в вашем аккаунте BotFather), укажите название и URL.

-------------------------------------------------------------------------------

3) Открытие Mini App:

- Кнопка меню бота
- Deep‑link: `https://t.me/<bot_username>?startapp=payload`

---

### Покупка домена и настройка DNS

1) Купите домен у любого регистратора.

2) Укажите DNS‑серверы регистратора или используйте Cloudflare DNS (удобно для проксирования и управления).

3) Создайте A‑запись на корень домена и/или поддомен:

@       A   <ВАШ_ПУБЛИЧНЫЙ_IP>
www     CNAME   @       (опционально)
app     A   <ВАШ_ПУБЛИЧНЫЙ_IP> (если хотите поддомен)

4) Дождитесь обновления DNS (обычно 5–30 минут).

### Установка Nginx и выдача SSL‑сертификата
На сервере Ubuntu:
```bash
sudo apt update && sudo apt install -y nginx

# Откройте firewall (если включён UFW)
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable   # осторожно: убедитесь, что SSH правило добавлено

# Установите certbot и плагин для Nginx
sudo apt install -y certbot python3-certbot-nginx

# Выпустите сертификат (замените example.com на ваш домен)
sudo certbot --nginx -d example.com -d www.example.com

# Автопродление проверьте командой
sudo certbot renew --dry-run
```
Если вы используете Cloudflare с проксированием (оранжевая туча), либо отключите прокси на время выпуска, либо используйте DNS‑плагин Certbot.