"""
Веб-API для взаимодействия игры с данными пользователей
Поддерживает авторизацию, магазин, рефералы и лидерборд
"""

import json
import hashlib
import hmac
import jwt
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from db.database import DatabaseManager
import os

# Секретный ключ бота для проверки подлинности запросов
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
JWT_SECRET = os.getenv("JWT_SECRET", BOT_TOKEN or "default_secret_key_change_in_production")
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")  # Токен от платежного провайдера
# Инициализируем базу данных
db_manager = DatabaseManager()

class GameAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обработка GET запросов"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        # Добавляем CORS заголовки
        self._add_cors_headers()
        
        # Маршрутизация GET запросов
        if path == '/api/user/profile':
            self.handle_get_profile(query_params)
        elif path == '/api/user/stats':
            self.handle_get_stats(query_params)
        elif path == '/api/shop/items':
            self.handle_get_shop_items(query_params)
        elif path == '/api/upgrades/list':
            self.handle_get_upgrades(query_params)
        elif path == '/api/referral/link':
            self.handle_get_referral_link(query_params)
        elif path == '/api/referral/stats':
            self.handle_get_referral_stats(query_params)
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_POST(self):
        """Обработка POST запросов"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Добавляем CORS заголовки
        self._add_cors_headers()
        
        # Читаем тело запроса
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            request_data = json.loads(post_data)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return
        
        # Маршрутизация POST запросов
        if path == '/api/auth/login':
            self.handle_login(request_data)
        elif path == '/api/shop/buy':
            self.handle_buy_upgrade(request_data)
        elif path == '/api/upgrades/apply':
            self.handle_apply_upgrade(request_data)
        elif path == '/api/referral/claim':
            self.handle_claim_referral(request_data)
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_OPTIONS(self):
        """Обработка OPTIONS запросов для CORS"""
        self.send_response(200)
        self._add_cors_headers()
        self.end_headers()
    
    def _add_cors_headers(self):
        """Добавить CORS заголовки"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def _send_json_response(self, data: dict, status_code: int = 200):
        """Отправить JSON ответ"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self._add_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def _get_user_from_auth(self, request_data: dict) -> int:
        """Получить user_id из данных авторизации"""
        # Проверяем JWT токен
        auth_header = self.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
                return payload.get('user_id')
            except jwt.InvalidTokenError:
                pass
        
        # Fallback на старый метод через Telegram WebApp данные
        if 'user_id' in request_data:
            return request_data['user_id']
        
        return None
    
    # === ЭНДПОИНТЫ АВТОРИЗАЦИИ ===
    
    def handle_login(self, request_data):
        """Авторизация через Telegram WebApp"""
        try:
            # Проверяем данные Telegram WebApp
            if not self.verify_telegram_data_from_request(request_data):
                self._send_json_response({"success": False, "message": "Unauthorized"}, 401)
                return
            
            user_id = request_data.get('user_id')
            telegram_data = request_data.get('user_data', {})
            
            if not user_id:
                self._send_json_response({"success": False, "message": "Invalid user_id"}, 400)
                return
            
            # Инициализируем пользователя
            db_manager.create_or_update_user(user_id, telegram_data)
            
            # Создаем JWT токен
            token_payload = {
                'user_id': user_id,
                'telegram_id': user_id,
                'exp': int(time.time()) + 86400  # 24 часа
            }
            token = jwt.encode(token_payload, JWT_SECRET, algorithm='HS256')
            
            user_info = db_manager.get_user_profile(user_id)
            
            self._send_json_response({
                "success": True,
                "token": token,
                "user": user_info
            })
            
        except Exception as e:
            self._send_json_response({"success": False, "message": f"Server error: {str(e)}"}, 500)

    # === ЭНДПОИНТЫ ПОЛЬЗОВАТЕЛЯ ===
    
    def handle_get_profile(self, query_params):
        """Получить профиль пользователя"""
        try:
            if not self.verify_telegram_data(query_params):
                self._send_json_response({"success": False, "message": "Unauthorized"}, 401)
                return
            
            user_id = int(query_params.get('user_id', [0])[0])
            if user_id == 0:
                self._send_json_response({"success": False, "message": "Invalid user_id"}, 400)
                return
            
            profile = db_manager.get_user_profile(user_id)
            self._send_json_response({"success": True, "data": profile})
            
        except Exception as e:
            self._send_json_response({"success": False, "message": f"Server error: {str(e)}"}, 500)
    
    def handle_get_stats(self, query_params):
        """Получить статистику игрока"""
        try:
            if not self.verify_telegram_data(query_params):
                self._send_json_response({"success": False, "message": "Unauthorized"}, 401)
                return
            
            user_id = int(query_params.get('user_id', [0])[0])
            if user_id == 0:
                self._send_json_response({"success": False, "message": "Invalid user_id"}, 400)
                return
            
            user_info = db_manager.get_user_profile(user_id)
            stats = {
                "coins": user_info["coins"],
                "total_earned": user_info["total_earned"],
                "total_spent": user_info["total_spent"],
                "total_clicks": user_info["total_clicks"],
                "click_power": user_info["click_power"],
                "passive_income": user_info["passive_income"],
                "referrals_count": user_info["referrals_count"],
                "referral_earnings": user_info["referral_earnings"]
            }
            
            self._send_json_response({"success": True, "data": stats})
            
        except Exception as e:
            self._send_json_response({"success": False, "message": f"Server error: {str(e)}"}, 500)


    # === ЭНДПОИНТЫ МАГАЗИНА ===
    
    def handle_get_shop_items(self, query_params):
        """Получить список предметов в магазине"""
        try:
            if not self.verify_telegram_data(query_params):
                self._send_json_response({"success": False, "message": "Unauthorized"}, 401)
                return
            
            user_id = int(query_params.get('user_id', [0])[0])
            if user_id == 0:
                self._send_json_response({"success": False, "message": "Invalid user_id"}, 400)
                return
            
            shop_items = db_manager.get_shop_items(user_id)
            self._send_json_response({"success": True, "data": shop_items})
            
        except Exception as e:
            self._send_json_response({"success": False, "message": f"Server error: {str(e)}"}, 500)
    
    def handle_buy_upgrade(self, request_data):
        """Купить улучшение"""
        try:
            user_id = self._get_user_from_auth(request_data)
            if not user_id:
                self._send_json_response({"success": False, "message": "Unauthorized"}, 401)
                return
            
            item_id = request_data.get('item_id')
            if not item_id:
                self._send_json_response({"success": False, "message": "Missing item_id"}, 400)
                return
            
            result = db_manager.buy_upgrade(user_id, item_id)
            status_code = 200 if result["success"] else 400
            self._send_json_response(result, status_code)
            
        except Exception as e:
            self._send_json_response({"success": False, "message": f"Server error: {str(e)}"}, 500)
    
    def handle_get_upgrades(self, query_params):
        """Получить список улучшений пользователя"""
        try:
            if not self.verify_telegram_data(query_params):
                self._send_json_response({"success": False, "message": "Unauthorized"}, 401)
                return
            
            user_id = int(query_params.get('user_id', [0])[0])
            if user_id == 0:
                self._send_json_response({"success": False, "message": "Invalid user_id"}, 400)
                return
            
            upgrades = db_manager.get_user_upgrades(user_id)
            self._send_json_response({"success": True, "data": upgrades})
            
        except Exception as e:
            self._send_json_response({"success": False, "message": f"Server error: {str(e)}"}, 500)
    
    def handle_apply_upgrade(self, request_data):
        """Применить улучшение (заглушка для будущего функционала)"""
        try:
            user_id = self._get_user_from_auth(request_data)
            if not user_id:
                self._send_json_response({"success": False, "message": "Unauthorized"}, 401)
                return
            
            # В текущей реализации улучшения применяются автоматически при покупке
            self._send_json_response({
                "success": True,
                "message": "Upgrades are applied automatically upon purchase"
            })
            
        except Exception as e:
            self._send_json_response({"success": False, "message": f"Server error: {str(e)}"}, 500)


    # === ЭНДПОИНТЫ РЕФЕРАЛОВ ===
    
    def handle_get_referral_link(self, query_params):
        """Получить реферальную ссылку"""
        try:
            if not self.verify_telegram_data(query_params):
                self._send_json_response({"success": False, "message": "Unauthorized"}, 401)
                return
            
            user_id = int(query_params.get('user_id', [0])[0])
            if user_id == 0:
                self._send_json_response({"success": False, "message": "Invalid user_id"}, 400)
                return
            
            referral_link = db_manager.generate_referral_link(user_id)
            self._send_json_response({
                "success": True,
                "data": {"referral_link": referral_link}
            })
            
        except Exception as e:
            self._send_json_response({"success": False, "message": f"Server error: {str(e)}"}, 500)
    
    def handle_get_referral_stats(self, query_params):
        """Получить статистику рефералов"""
        try:
            if not self.verify_telegram_data(query_params):
                self._send_json_response({"success": False, "message": "Unauthorized"}, 401)
                return
            
            user_id = int(query_params.get('user_id', [0])[0])
            if user_id == 0:
                self._send_json_response({"success": False, "message": "Invalid user_id"}, 400)
                return
            
            referral_stats = db_manager.get_referral_stats(user_id)
            self._send_json_response({"success": True, "data": referral_stats})
            
        except Exception as e:
            self._send_json_response({"success": False, "message": f"Server error: {str(e)}"}, 500)
    
    def handle_claim_referral(self, request_data):
        """Получить награду за реферала (заглушка)"""
        try:
            user_id = self._get_user_from_auth(request_data)
            if not user_id:
                self._send_json_response({"success": False, "message": "Unauthorized"}, 401)
                return
            
            # В текущей реализации награды за рефералов начисляются автоматически
            self._send_json_response({
                "success": True,
                "message": "Referral rewards are granted automatically"
            })
            
        except Exception as e:
            self._send_json_response({"success": False, "message": f"Server error: {str(e)}"}, 500)

    # === ЭНДПОИНТ ЛИДЕРБОРДА ===
    
    def handle_get_leaderboard(self, query_params):
        """Получить таблицу лидеров"""
        try:
            limit = int(query_params.get('limit', [10])[0])
            limit = min(max(limit, 1), 100)  # Ограничиваем от 1 до 100
            
            leaderboard = db_manager.get_leaderboard(limit)
            self._send_json_response({"success": True, "data": leaderboard})
            
        except Exception as e:
            self._send_json_response({"success": False, "message": f"Server error: {str(e)}"}, 500)

    # === МЕТОДЫ АВТОРИЗАЦИИ ===
    
    def verify_telegram_data(self, query_params):
        """Проверка подлинности данных от Telegram WebApp (GET запросы)"""
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
    
    def verify_telegram_data_from_request(self, request_data):
        """Проверка подлинности данных от Telegram WebApp (POST запросы)"""
        # Упрощенная проверка для демонстрации
        # В реальном проекте нужна полная проверка подписи
        
        # Проверяем наличие обязательных параметров
        if 'user_id' not in request_data:
            return False
        
        # Здесь должна быть проверка подписи hash от Telegram
        # Для простоты пропускаем эту проверку в демо-версии
        return True

def start_api_server(port=8080):
    """Запуск API сервера"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, GameAPIHandler)
    print(f"[INFO] API Server starting on port {port}")
    print(f"[INFO] Available endpoints:")
    print(f"")
    print(f"[AUTH] Авторизация:")
    print(f"   POST /api/auth/login          - Авторизация через Telegram WebApp")
    print(f"")
    print(f"[USER] Пользователь:")
    print(f"   GET  /api/user/profile        - Получить профиль пользователя")
    print(f"   GET  /api/user/stats          - Статистика игрока")
    print(f"")
    print(f"[GAME] Игровой процесс:")
    print(f"   GET  /api/shop/items          - Список доступных улучшений")
    print(f"   POST /api/shop/buy            - Купить улучшение")
    print(f"   GET  /api/upgrades/list       - Список улучшений игрока")
    print(f"   POST /api/upgrades/apply      - Применить улучшение")
    print(f"")
    print(f"[REF] Реферальная система:")
    print(f"   GET  /api/referral/link       - Получить реферальную ссылку")
    print(f"   GET  /api/referral/stats      - Статистика рефералов")
    print(f"   POST /api/referral/claim      - Получить награду за реферала")
    print(f"")
    print(f"[TIP] Для POST запросов используйте JWT токен в заголовке Authorization: Bearer <token>")
    httpd.serve_forever()

if __name__ == "__main__":
    start_api_server()
