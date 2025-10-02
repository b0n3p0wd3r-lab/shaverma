"""
Модуль для работы с SQLite базой данных
Обеспечивает все операции с данными пользователей
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager

# Путь к базе данных
DB_PATH = Path(__file__).parent / "clicker_game.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

class DatabaseManager:
    """Менеджер для работы с SQLite базой данных"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        if not self.db_path.exists():
            print(f"[INFO] Создание новой базы данных: {self.db_path}")
        
        # Создаем таблицы из схемы
        if SCHEMA_PATH.exists():
            with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                schema = f.read()
            
            with self.get_connection() as conn:
                conn.executescript(schema)
                conn.commit()
                print("[OK] База данных инициализирована")
        else:
            print("[ERROR] Файл схемы не найден!")
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для подключения к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Позволяет обращаться к колонкам по имени
        try:
            yield conn
        finally:
            conn.close()
    
    # === МЕТОДЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ===
    
    def create_user(self, user_id: int, telegram_data: Dict = None) -> bool:
        """Создать нового пользователя"""
        current_time = time.time()
        
        with self.get_connection() as conn:
            try:
                # Создаем пользователя
                conn.execute("""
                    INSERT OR IGNORE INTO users 
                    (user_id, telegram_id, username, first_name, registration_date, last_active, referrer_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    user_id,  # telegram_id = user_id
                    telegram_data.get('username', '') if telegram_data else '',
                    telegram_data.get('first_name', '') if telegram_data else '',
                    current_time,
                    current_time,
                    telegram_data.get('referrer_id') if telegram_data else None
                ))
                
                # Создаем игровое состояние
                conn.execute("""
                    INSERT OR IGNORE INTO game_state 
                    (user_id, coins, total_earned, total_spent, total_clicks, 
                     click_power, passive_income, last_passive_collection)
                    VALUES (?, 0, 0, 0, 0, 1, 0, ?)
                """, (user_id, current_time))
                
                conn.commit()
                return True
                
            except sqlite3.Error as e:
                print(f"Ошибка создания пользователя: {e}")
                return False
    
    def create_or_update_user(self, user_id: int, telegram_data: Dict = None) -> bool:
        """Создать или обновить пользователя"""
        existing_user = self.get_user(user_id)
        if existing_user:
            # Обновляем данные существующего пользователя
            self.update_user_activity(user_id)
            if telegram_data:
                with self.get_connection() as conn:
                    conn.execute("""
                        UPDATE users 
                        SET username = ?, first_name = ?
                        WHERE user_id = ?
                    """, (
                        telegram_data.get('username', ''),
                        telegram_data.get('first_name', ''),
                        user_id
                    ))
                    conn.commit()
            return True
        else:
            # Создаем нового пользователя
            return self.create_user(user_id, telegram_data)
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить данные пользователя"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT u.*, gs.* FROM users u
                LEFT JOIN game_state gs ON u.user_id = gs.user_id
                WHERE u.user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_user_profile(self, user_id: int) -> Dict:
        """Получить профиль пользователя для API"""
        user_data = self.get_user(user_id)
        if not user_data:
            # Создаем пользователя если не существует
            self.create_user(user_id)
            user_data = self.get_user(user_id)
        
        if user_data:
            return {
                "user_id": user_data.get("user_id", user_id),
                "telegram_id": user_data.get("telegram_id", user_id),
                "username": user_data.get("username", ""),
                "first_name": user_data.get("first_name", ""),
                "coins": user_data.get("coins", 0),
                "total_earned": user_data.get("total_earned", 0),
                "total_spent": user_data.get("total_spent", 0),
                "total_clicks": user_data.get("total_clicks", 0),
                "click_power": user_data.get("click_power", 1),
                "passive_income": user_data.get("passive_income", 0),
                "registration_date": user_data.get("registration_date", time.time()),
                "last_active": user_data.get("last_active", time.time()),
                "total_purchases": 0,  # TODO: подсчитать из транзакций
                "referrals_count": self._get_referrals_count(user_id),
                "referral_earnings": self._get_referral_earnings(user_id)
            }
        return {}
    
    def update_user_activity(self, user_id: int):
        """Обновить время последней активности"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE users SET last_active = ? WHERE user_id = ?
            """, (time.time(), user_id))
            conn.commit()
    
    # === МЕТОДЫ ДЛЯ ИГРОВОГО СОСТОЯНИЯ ===
    
    def update_coins(self, user_id: int, amount: int, transaction_type: str = 'manual', 
                     description: str = None, item_id: str = None) -> bool:
        """Обновить количество монет пользователя"""
        with self.get_connection() as conn:
            try:
                # Обновляем баланс
                if amount > 0:
                    conn.execute("""
                        UPDATE game_state 
                        SET coins = coins + ?, total_earned = total_earned + ?
                        WHERE user_id = ?
                    """, (amount, amount, user_id))
                else:
                    conn.execute("""
                        UPDATE game_state 
                        SET coins = coins + ?, total_spent = total_spent + ?
                        WHERE user_id = ?
                    """, (amount, abs(amount), user_id))
                
                # Записываем транзакцию
                conn.execute("""
                    INSERT INTO transactions 
                    (user_id, transaction_type, amount, description, item_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, transaction_type, amount, description, item_id, time.time()))
                
                conn.commit()
                return True
                
            except sqlite3.Error as e:
                print(f"Ошибка обновления монет: {e}")
                return False
    
    def add_coins(self, user_id: int, amount: int, transaction_id: str = None, transaction_type: str = "purchase") -> int:
        """Добавить монеты пользователю (обертка для update_coins)"""
        success = self.update_coins(user_id, amount, transaction_type, f"Purchase: {transaction_id}")
        if success:
            # Возвращаем новый баланс
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT coins FROM game_state WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
                return row['coins'] if row else 0
        return 0
    
    def update_click_stats(self, user_id: int, clicks: int = 1):
        """Обновить статистику кликов"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE game_state 
                SET total_clicks = total_clicks + ?
                WHERE user_id = ?
            """, (clicks, user_id))
            conn.commit()
    
    def get_user_balance(self, user_id: int) -> int:
        """Получить баланс пользователя"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT coins FROM game_state WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            return row['coins'] if row else 0
    
    # === МЕТОДЫ ДЛЯ УЛУЧШЕНИЙ ===
    
    def get_user_upgrades(self, user_id: int) -> List[Dict]:
        """Получить список улучшений пользователя для API"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT upgrade_id, level, purchased_at FROM user_upgrades 
                WHERE user_id = ? ORDER BY purchased_at DESC
            """, (user_id,))
            
            upgrades = []
            for row in cursor.fetchall():
                upgrades.append({
                    'upgrade_id': row['upgrade_id'],
                    'level': row['level'],
                    'purchased_at': row['purchased_at']
                })
            
            return upgrades
    
    def buy_upgrade(self, user_id: int, item_id: str) -> Dict:
        """Купить улучшение (обновленная версия для API)"""
        # Получаем информацию о предмете из магазина
        shop_items = self.get_shop_items(user_id)
        item = next((item for item in shop_items if item['id'] == item_id), None)
        
        if not item:
            return {"success": False, "message": "Предмет не найден"}
        
        if not item['available']:
            return {"success": False, "message": "Предмет недоступен для покупки"}
        
        with self.get_connection() as conn:
            try:
                # Проверяем баланс
                cursor = conn.execute("SELECT coins FROM game_state WHERE user_id = ?", (user_id,))
                row = cursor.fetchone()
                if not row or row['coins'] < item['price']:
                    return {"success": False, "message": "Недостаточно монет"}
                
                # Получаем текущий уровень
                cursor = conn.execute("""
                    SELECT level FROM user_upgrades WHERE user_id = ? AND upgrade_id = ?
                """, (user_id, item_id))
                
                current_row = cursor.fetchone()
                current_level = current_row['level'] if current_row else 0
                new_level = current_level + 1
                
                # Обновляем или создаем запись об улучшении
                if current_row:
                    conn.execute("""
                        UPDATE user_upgrades 
                        SET level = ?, purchased_at = ?
                        WHERE user_id = ? AND upgrade_id = ?
                    """, (new_level, time.time(), user_id, item_id))
                else:
                    conn.execute("""
                        INSERT INTO user_upgrades (user_id, upgrade_id, level, purchased_at)
                        VALUES (?, ?, ?, ?)
                    """, (user_id, item_id, new_level, time.time()))
                
                # Применяем эффект улучшения
                if item['effect_type'] and item['effect_value']:
                    if item['effect_type'] == "click_power":
                        conn.execute("""
                            UPDATE game_state 
                            SET click_power = click_power + ?
                            WHERE user_id = ?
                        """, (item['effect_value'], user_id))
                    elif item['effect_type'] == "passive_income":
                        conn.execute("""
                            UPDATE game_state 
                            SET passive_income = passive_income + ?
                            WHERE user_id = ?
                        """, (item['effect_value'], user_id))
                
                # Списываем монеты
                conn.execute("""
                    UPDATE game_state 
                    SET coins = coins - ?, total_spent = total_spent + ?
                    WHERE user_id = ?
                """, (item['price'], item['price'], user_id))
                
                # Записываем транзакцию
                conn.execute("""
                    INSERT INTO transactions 
                    (user_id, transaction_type, amount, item_id, created_at)
                    VALUES (?, 'upgrade_purchase', ?, ?, ?)
                """, (user_id, -item['price'], item_id, time.time()))
                
                conn.commit()
                
                # Получаем обновленные данные
                new_balance = self.get_user_balance(user_id)
                user_stats = self.get_user_profile(user_id)
                
                return {
                    "success": True,
                    "message": f"Улучшение '{item['name']}' куплено!",
                    "data": {
                        "item": item,
                        "new_level": new_level,
                        "new_balance": new_balance,
                        "user_stats": {
                            "click_power": user_stats['click_power'],
                            "passive_income": user_stats['passive_income']
                        }
                    }
                }
                
            except sqlite3.Error as e:
                print(f"Ошибка покупки улучшения: {e}")
                return {"success": False, "message": "Ошибка сервера"}
    
    def get_shop_items(self, user_id: int) -> List[Dict]:
        """Получить список предметов в магазине"""
        # Получаем текущие улучшения пользователя
        user_upgrades = {}
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT upgrade_id, level FROM user_upgrades WHERE user_id = ?
            """, (user_id,))
            user_upgrades = {row['upgrade_id']: row['level'] for row in cursor.fetchall()}
        
        # Список доступных улучшений
        shop_items = [
            {
                "id": "click_power_1",
                "name": "Улучшенный клик",
                "description": "+1 монета за клик",
                "price": 50,
                "effect_type": "click_power",
                "effect_value": 1,
                "category": "click",
                "max_level": 50
            },
            {
                "id": "click_power_5",
                "name": "Мощный клик",
                "description": "+5 монет за клик",
                "price": 200,
                "effect_type": "click_power",
                "effect_value": 5,
                "category": "click",
                "max_level": 20
            },
            {
                "id": "passive_income_1",
                "name": "Пассивный доход",
                "description": "+1 монета в секунду",
                "price": 100,
                "effect_type": "passive_income",
                "effect_value": 1,
                "category": "passive",
                "max_level": 100
            },
            {
                "id": "passive_income_10",
                "name": "Мега-генератор",
                "description": "+10 монет в секунду",
                "price": 1000,
                "effect_type": "passive_income",
                "effect_value": 10,
                "category": "passive",
                "max_level": 50
            }
        ]
        
        # Обогащаем данные о предметах
        for item in shop_items:
            current_level = user_upgrades.get(item['id'], 0)
            item['current_level'] = current_level
            item['available'] = current_level < item['max_level']
            item['price'] = int(item['price'] * (1.1 ** current_level))  # Цена растет с каждым уровнем
        
        return shop_items
    
    
    # === МЕТОДЫ ДЛЯ РЕФЕРАЛОВ ===
    
    def add_referral(self, referrer_id: int, referred_id: int, bonus: int = 100) -> bool:
        """Добавить реферала"""
        with self.get_connection() as conn:
            try:
                # Проверяем, что реферал еще не добавлен
                cursor = conn.execute("""
                    SELECT id FROM referrals 
                    WHERE referrer_id = ? AND referred_id = ?
                """, (referrer_id, referred_id))
                
                if cursor.fetchone():
                    return False  # Уже существует
                
                # Добавляем реферала
                conn.execute("""
                    INSERT INTO referrals (referrer_id, referred_id, created_at, bonus_paid)
                    VALUES (?, ?, ?, ?)
                """, (referrer_id, referred_id, time.time(), bonus))
                
                # Обновляем реферера в таблице пользователей
                conn.execute("""
                    UPDATE users SET referrer_id = ? WHERE user_id = ?
                """, (referrer_id, referred_id))
                
                # Начисляем бонус рефереру
                conn.execute("""
                    UPDATE game_state 
                    SET coins = coins + ?, total_earned = total_earned + ?
                    WHERE user_id = ?
                """, (bonus, bonus, referrer_id))
                
                # Записываем транзакцию
                conn.execute("""
                    INSERT INTO transactions 
                    (user_id, transaction_type, amount, description, created_at)
                    VALUES (?, 'referral_bonus', ?, ?, ?)
                """, (referrer_id, bonus, f"Реферал {referred_id}", time.time()))
                
                conn.commit()
                return True
                
            except sqlite3.Error as e:
                print(f"Ошибка добавления реферала: {e}")
                return False
    
    def get_referral_stats(self, user_id: int) -> Dict:
        """Получить статистику рефералов"""
        with self.get_connection() as conn:
            # Получаем рефералов
            cursor = conn.execute("""
                SELECT r.referred_id, r.created_at, r.bonus_paid,
                       u.username, u.first_name, gs.total_earned
                FROM referrals r
                LEFT JOIN users u ON r.referred_id = u.user_id
                LEFT JOIN game_state gs ON r.referred_id = gs.user_id
                WHERE r.referrer_id = ?
                ORDER BY r.created_at DESC
            """, (user_id,))
            
            referrals = []
            total_earnings = 0
            
            for row in cursor.fetchall():
                referrals.append({
                    'user_id': row['referred_id'],
                    'username': row['username'] or '',
                    'first_name': row['first_name'] or '',
                    'registration_date': row['created_at'],
                    'total_earned': row['total_earned'] or 0
                })
                total_earnings += row['bonus_paid'] or 0
            
            return {
                'total_referrals': len(referrals),
                'total_earnings': total_earnings,
                'referrals': referrals
            }
    
    def generate_referral_link(self, user_id: int) -> str:
        """Генерировать реферальную ссылку"""
        # Простая реализация - в реальном проекте может быть сложнее
        return f"https://t.me/your_bot_name?start=ref_{user_id}"
    
    def _get_referrals_count(self, user_id: int) -> int:
        """Получить количество рефералов пользователя"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) as count FROM referrals WHERE referrer_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    def _get_referral_earnings(self, user_id: int) -> int:
        """Получить доходы от рефералов"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT SUM(bonus_paid) as total FROM referrals WHERE referrer_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return row['total'] if row and row['total'] else 0
    
    # === МЕТОДЫ ДЛЯ ЛИДЕРБОРДА ===
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Получить таблицу лидеров"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT u.user_id, u.username, u.first_name,
                       gs.total_earned, gs.total_clicks, gs.coins
                FROM users u
                LEFT JOIN game_state gs ON u.user_id = gs.user_id
                ORDER BY gs.total_earned DESC
                LIMIT ?
            """, (limit,))
            
            leaderboard = []
            for i, row in enumerate(cursor.fetchall(), 1):
                leaderboard.append({
                    'position': i,
                    'user_id': row['user_id'],
                    'username': row['username'] or '',
                    'first_name': row['first_name'] or '',
                    'total_earned': row['total_earned'] or 0,
                    'total_clicks': row['total_clicks'] or 0,
                    'coins': row['coins'] or 0
                })
            
            return leaderboard
    
    # === МЕТОДЫ ДЛЯ ПОКУПОК МОНЕТ ===
    
    def add_coin_purchase(self, user_id: int, amount: int, price_rub: int, 
                         telegram_payment_id: str) -> bool:
        """Записать покупку монет за реальные деньги"""
        with self.get_connection() as conn:
            try:
                # Записываем покупку
                conn.execute("""
                    INSERT INTO coin_purchases 
                    (user_id, amount, price_rub, telegram_payment_id, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, amount, price_rub, telegram_payment_id, time.time()))
                
                # Начисляем монеты
                conn.execute("""
                    UPDATE game_state 
                    SET coins = coins + ?, total_earned = total_earned + ?
                    WHERE user_id = ?
                """, (amount, amount, user_id))
                
                # Записываем транзакцию
                conn.execute("""
                    INSERT INTO transactions 
                    (user_id, transaction_type, amount, description, transaction_id, created_at)
                    VALUES (?, 'purchase', ?, ?, ?, ?)
                """, (user_id, amount, f"Покупка за {price_rub}₽", telegram_payment_id, time.time()))
                
                conn.commit()
                return True
                
            except sqlite3.Error as e:
                print(f"Ошибка записи покупки: {e}")
                return False

# Глобальный экземпляр менеджера базы данных
db_manager = DatabaseManager()
