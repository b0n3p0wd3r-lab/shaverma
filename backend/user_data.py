"""
Модуль для работы с данными пользователей
Здесь хранится информация о балансе монет пользователей
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional

# Путь к файлу с данными пользователей
USER_DATA_FILE = Path(__file__).parent / "user_data.json"

class UserDataManager:
    def __init__(self):
        self.data: Dict[str, Dict] = {}
        self.load_data()
    
    def load_data(self):
        """Загрузить данные пользователей из файла"""
        if USER_DATA_FILE.exists():
            try:
                with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.data = {}
        else:
            self.data = {}
    
    def save_data(self):
        """Сохранить данные пользователей в файл"""
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def get_user_coins(self, user_id: int) -> int:
        """Получить количество монет пользователя"""
        user_str = str(user_id)
        if user_str not in self.data:
            self.data[user_str] = {"coins": 0, "purchases": []}
            self.save_data()
        return self.data[user_str].get("coins", 0)
    
    def add_coins(self, user_id: int, amount: int, transaction_id: str = None) -> int:
        """Добавить монеты пользователю"""
        user_str = str(user_id)
        if user_str not in self.data:
            self.data[user_str] = {"coins": 0, "purchases": []}
        
        self.data[user_str]["coins"] += amount
        
        # Записываем информацию о покупке
        if transaction_id:
            purchase_info = {
                "amount": amount,
                "transaction_id": transaction_id,
                "timestamp": __import__('time').time()
            }
            self.data[user_str]["purchases"].append(purchase_info)
        
        self.save_data()
        return self.data[user_str]["coins"]
    
    def spend_coins(self, user_id: int, amount: int) -> bool:
        """Потратить монеты пользователя"""
        user_str = str(user_id)
        current_coins = self.get_user_coins(user_id)
        
        if current_coins >= amount:
            self.data[user_str]["coins"] -= amount
            self.save_data()
            return True
        return False
    
    def get_user_info(self, user_id: int) -> Dict:
        """Получить полную информацию о пользователе"""
        user_str = str(user_id)
        if user_str not in self.data:
            self.data[user_str] = {"coins": 0, "purchases": []}
            self.save_data()
        
        return {
            "user_id": user_id,
            "coins": self.data[user_str]["coins"],
            "total_purchases": len(self.data[user_str]["purchases"])
        }

# Глобальный экземпляр менеджера данных
user_manager = UserDataManager()
