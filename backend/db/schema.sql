-- SQLite схема для Clicker Game
-- Создание всех необходимых таблиц для игры

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    registration_date REAL NOT NULL,
    last_active REAL NOT NULL,
    referrer_id INTEGER,
    FOREIGN KEY (referrer_id) REFERENCES users(user_id)
);

-- Игровое состояние пользователей
CREATE TABLE IF NOT EXISTS game_state (
    user_id INTEGER PRIMARY KEY,
    coins INTEGER DEFAULT 0,
    total_earned INTEGER DEFAULT 0,
    total_spent INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    click_power INTEGER DEFAULT 1,
    passive_income INTEGER DEFAULT 0,
    last_passive_collection REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Улучшения пользователей
CREATE TABLE IF NOT EXISTS user_upgrades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    upgrade_id TEXT NOT NULL,
    level INTEGER DEFAULT 1,
    purchased_at REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE(user_id, upgrade_id)
);

-- Достижения пользователей
CREATE TABLE IF NOT EXISTS user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    achievement_id TEXT NOT NULL,
    unlocked_at REAL,
    claimed_at REAL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE(user_id, achievement_id)
);

-- Рефералы
CREATE TABLE IF NOT EXISTS referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL,
    referred_id INTEGER NOT NULL,
    created_at REAL NOT NULL,
    bonus_paid INTEGER DEFAULT 0,
    FOREIGN KEY (referrer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (referred_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE(referrer_id, referred_id)
);

-- Транзакции (все операции с монетами)
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    transaction_type TEXT NOT NULL, -- 'purchase', 'upgrade_buy', 'achievement_reward', 'referral_bonus', 'click_earning'
    amount INTEGER NOT NULL, -- может быть отрицательным для трат
    description TEXT,
    item_id TEXT, -- для покупок улучшений
    achievement_id TEXT, -- для наград за достижения
    transaction_id TEXT, -- внешний ID (например, от Telegram Payments)
    created_at REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Покупки монет за реальные деньги
CREATE TABLE IF NOT EXISTS coin_purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    price_rub INTEGER NOT NULL,
    telegram_payment_id TEXT UNIQUE,
    created_at REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active);
CREATE INDEX IF NOT EXISTS idx_game_state_total_earned ON game_state(total_earned DESC);
CREATE INDEX IF NOT EXISTS idx_user_upgrades_user_id ON user_upgrades(user_id);
CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);

-- Триггеры для автоматического обновления статистики

-- Обновление last_active при любых изменениях в game_state
CREATE TRIGGER IF NOT EXISTS update_last_active_on_game_state
    AFTER UPDATE ON game_state
    BEGIN
        UPDATE users SET last_active = (julianday('now') - 2440587.5) * 86400.0 
        WHERE user_id = NEW.user_id;
    END;

-- Обновление статистики при покупке улучшений
CREATE TRIGGER IF NOT EXISTS update_stats_on_upgrade_purchase
    AFTER INSERT ON user_upgrades
    BEGIN
        UPDATE users SET last_active = (julianday('now') - 2440587.5) * 86400.0 
        WHERE user_id = NEW.user_id;
    END;

-- Обновление статистики при получении достижений
CREATE TRIGGER IF NOT EXISTS update_stats_on_achievement_claim
    AFTER UPDATE OF claimed_at ON user_achievements
    WHEN NEW.claimed_at IS NOT NULL AND OLD.claimed_at IS NULL
    BEGIN
        UPDATE users SET last_active = (julianday('now') - 2440587.5) * 86400.0 
        WHERE user_id = NEW.user_id;
    END;
