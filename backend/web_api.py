"""
Простой веб-API для взаимодействия игры с данными пользователей
"""

import json
import hashlib
import hmac
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from user_data import user_manager
import os

# Секретный ключ бота для проверки подлинности запросов
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

class GameAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обработка GET запросов"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        # Добавляем CORS заголовки
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        if path == '/api/user/balance':
            self.handle_get_balance(query_params)
        elif path == '/api/user/spend':
            self.handle_spend_coins(query_params)
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_OPTIONS(self):
        """Обработка OPTIONS запросов для CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_get_balance(self, query_params):
        """Получить баланс пользователя"""
        try:
            # Проверяем параметры Telegram WebApp
            if not self.verify_telegram_data(query_params):
                self.send_error(401, "Unauthorized")
                return
            
            user_id = int(query_params.get('user_id', [0])[0])
            if user_id == 0:
                self.send_error(400, "Invalid user_id")
                return
            
            user_info = user_manager.get_user_info(user_id)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "success": True,
                "data": user_info
            }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
    
    def handle_spend_coins(self, query_params):
        """Потратить монеты пользователя"""
        try:
            # Проверяем параметры Telegram WebApp
            if not self.verify_telegram_data(query_params):
                self.send_error(401, "Unauthorized")
                return
            
            user_id = int(query_params.get('user_id', [0])[0])
            amount = int(query_params.get('amount', [0])[0])
            
            if user_id == 0 or amount <= 0:
                self.send_error(400, "Invalid parameters")
                return
            
            success = user_manager.spend_coins(user_id, amount)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            if success:
                user_info = user_manager.get_user_info(user_id)
                response = {
                    "success": True,
                    "message": f"Spent {amount} coins",
                    "data": user_info
                }
            else:
                response = {
                    "success": False,
                    "message": "Insufficient coins"
                }
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
    
    def verify_telegram_data(self, query_params):
        """Проверка подлинности данных от Telegram WebApp"""
        # Упрощенная проверка для демонстрации
        # В реальном проекте нужна полная проверка подписи
        
        # Проверяем наличие обязательных параметров
        required_params = ['user_id', 'auth_date']
        for param in required_params:
            if param not in query_params:
                return False
        
        # Здесь должна быть проверка подписи hash от Telegram
        # Для простоты пропускаем эту проверку в демо-версии
        return True

def start_api_server(port=8080):
    """Запуск API сервера"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, GameAPIHandler)
    print(f"🌐 API Server starting on port {port}")
    print(f"📡 Available endpoints:")
    print(f"   GET /api/user/balance?user_id=123")
    print(f"   GET /api/user/spend?user_id=123&amount=10")
    httpd.serve_forever()

if __name__ == "__main__":
    start_api_server()
