"""Интеграция с AuthorToday API для получения отзывов."""
import requests
import time
from typing import List, Dict, Optional
from datetime import datetime
from utils.config import Config
# Импорты репозиториев перенесены в функцию для избежания циклических зависимостей
# Старые импорты удалены - теперь используется только Supabase SDK


class AuthorToday:
    """Класс для работы с AuthorToday API."""
    
    def __init__(self):
        self.api = Config.AUTHORTODAY_API_URL or "https://api.author.today"
        self.web_api = Config.AUTHORTODAY_WEB_URL or "https://author.today"
        self.token = "Bearer guest"
        self.user_id = None
        self.headers = {
            "authorization": self.token,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
            "Content-Type": "application/json"
        }
    
    def login(self, login: str, password: str) -> dict:
        """
        Авторизация в AuthorToday.
        
        Args:
            login: Логин пользователя
            password: Пароль пользователя
        
        Returns:
            Ответ от API
        """
        data = {
            "login": login,
            "password": password
        }
        
        try:
            response = requests.post(
                f"{self.api}/v1/account/login-by-password",
                json=data,
                headers=self.headers,
                timeout=10
            ).json()
            
            if "token" in response:
                self.token = response["token"]
                self.headers["authorization"] = f"Bearer {self.token}"
                account_info = self.get_account_info()
                if "id" in account_info:
                    self.user_id = account_info["id"]
            
            return response
        except Exception as e:
            print(f"❌ Ошибка авторизации в AuthorToday: {e}")
            return {"error": str(e)}
    
    def login_with_token(self, token: str) -> dict:
        """Авторизация с использованием токена."""
        self.token = token
        self.headers["authorization"] = f"Bearer {self.token}"
        response = self.get_account_info()
        if "id" in response:
            self.user_id = response["id"]
        return response
    
    def get_account_info(self) -> dict:
        """Получить информацию о текущем пользователе."""
        try:
            return requests.get(
                f"{self.api}/v1/account/current-user",
                headers=self.headers,
                timeout=10
            ).json()
        except Exception as e:
            print(f"❌ Ошибка получения информации о пользователе: {e}")
            return {"error": str(e)}
    
    def search(self, title: str) -> dict:
        """
        Поиск произведений по названию.
        
        Args:
            title: Название для поиска
        
        Returns:
            Результаты поиска
        """
        try:
            response = requests.get(
                f"{self.web_api}/search?q={title}",
                headers=self.headers,
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f"❌ Ошибка поиска в AuthorToday: {e}")
            return {"error": str(e)}
    
    def get_work_meta_info(self, work_id: int) -> dict:
        """
        Получить метаинформацию о произведении.
        
        Args:
            work_id: ID произведения в AuthorToday
        
        Returns:
            Метаинформация о произведении
        """
        try:
            return requests.get(
                f"{self.api}/v1/work/{work_id}/meta-info",
                headers=self.headers,
                timeout=10
            ).json()
        except Exception as e:
            print(f"❌ Ошибка получения информации о произведении: {e}")
            return {"error": str(e)}
    
    def get_work_reviews(self, work_id: int) -> List[Dict]:
        """
        Получить отзывы на произведение.
        
        Примечание: Нужно уточнить точный endpoint для получения отзывов.
        Возможные варианты:
        - /v1/work/{work_id}/reviews
        - /v1/work/{work_id}/comments
        - /web_api/work/{work_id}/reviews
        
        Args:
            work_id: ID произведения в AuthorToday
        
        Returns:
            Список отзывов
        """
        # Пробуем разные возможные endpoints
        possible_endpoints = [
            f"{self.api}/v1/work/{work_id}/reviews",
            f"{self.api}/v1/work/{work_id}/comments",
            f"{self.web_api}/work/{work_id}/reviews",
            f"{self.web_api}/work/{work_id}/comments",
        ]
        
        for endpoint in possible_endpoints:
            try:
                response = requests.get(
                    endpoint,
                    headers=self.headers,
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    # Адаптируйте под структуру ответа
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        # Возможные ключи: reviews, comments, items, data
                        return data.get("reviews", data.get("comments", data.get("items", data.get("data", []))))
            except:
                continue
        
        return []
    
    def search_book_and_get_reviews(self, book_title: str, author_name: str = None) -> List[Dict]:
        """
        Найти книгу по названию и получить отзывы.
        
        Args:
            book_title: Название книги
            author_name: Имя автора (опционально, для уточнения поиска)
        
        Returns:
            Список отзывов
        """
        # Поиск книги
        search_query = book_title
        if author_name:
            search_query = f"{book_title} {author_name}"
        
        search_results = self.search(search_query)
        
        if "error" in search_results:
            return []
        
        # Парсим результаты поиска
        # Структура ответа может отличаться, адаптируйте под реальный формат
        works = []
        if isinstance(search_results, dict):
            works = search_results.get("works", search_results.get("items", search_results.get("data", [])))
        elif isinstance(search_results, list):
            works = search_results
        
        all_reviews = []
        
        # Для каждого найденного произведения получаем отзывы
        for work in works[:3]:  # Ограничиваем до 3 результатов
            work_id = work.get("id") or work.get("workId") or work.get("work_id")
            if work_id:
                # Проверяем, что это нужная книга (по названию)
                work_title = work.get("title", "").lower()
                if book_title.lower() in work_title or work_title in book_title.lower():
                    reviews = self.get_work_reviews(work_id)
                    all_reviews.extend(reviews)
                    time.sleep(0.5)  # Задержка между запросами
        
        return all_reviews


def _parse_date(date_str: Optional[str]):
    """Парсинг даты из различных форматов."""
    if not date_str:
        return None
    
    try:
        # Пробуем ISO формат
        if "T" in str(date_str):
            return datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        # Другие форматы можно добавить при необходимости
    except:
        pass
    
    return None


def sync_reviews_from_author_today(book_id: Optional[int] = None) -> Dict:
    """
    Синхронизировать отзывы с AuthorToday API.
    
    Args:
        book_id: ID книги (если None, обновляются все книги)
    
    Returns:
        Словарь со статистикой обновления
    """
    from database.repository_supabase import BookRepositorySupabase, ReviewRepositorySupabase
    
    # Получаем учетные данные из конфигурации
    login = Config.AUTHORTODAY_LOGIN
    password = Config.AUTHORTODAY_PASSWORD
    
    if not login or not password:
        return {
            "success": False,
            "error": "AUTHORTODAY_LOGIN и AUTHORTODAY_PASSWORD должны быть установлены в .env файле",
            "message": "Настройте учетные данные AuthorToday в .env файле"
        }
    
    # Создаем экземпляр API и авторизуемся
    api = AuthorToday()
    login_result = api.login(login, password)
    
    if "error" in login_result or "token" not in login_result:
        return {
            "success": False,
            "error": "Ошибка авторизации в AuthorToday",
            "message": "Проверьте правильность логина и пароля"
        }
    
    if book_id:
        # Обновляем отзывы для одной книги
        book_data = BookRepositorySupabase.get_by_id(book_id)
        if not book_data:
            return {"success": False, "error": "Книга не найдена"}
        
        reviews_data = api.search_book_and_get_reviews(book_data.get("title", ""), book_data.get("author", ""))
        updated_count = 0
        
        for review_data in reviews_data:
            # Адаптируйте под структуру ответа API AuthorToday
            review_dict = {
                "book_id": book_id,
                "litres_review_id": str(review_data.get("id", "")),
                "author_name": review_data.get("author") or review_data.get("userName") or review_data.get("authorName") or "Анонимный читатель",
                "rating": review_data.get("rating") or review_data.get("score") or review_data.get("stars"),
                "text": review_data.get("text") or review_data.get("content") or review_data.get("comment") or review_data.get("reviewText"),
                "date": _parse_date(review_data.get("date") or review_data.get("createdAt") or review_data.get("created_at"))
            }
            
            ReviewRepositorySupabase.create_or_update(review_dict)
            updated_count += 1
        
        return {
            "success": True,
            "book_id": book_id,
            "reviews_updated": updated_count
        }
    else:
        # Обновляем отзывы для всех книг
        books_data = BookRepositorySupabase.get_all()
        stats = {
            "total_books": len(books_data),
            "updated_books": 0,
            "total_reviews": 0
        }
        
        for book_data in books_data:
            reviews_data = api.search_book_and_get_reviews(book_data.get("title", ""), book_data.get("author", ""))
            if reviews_data:
                for review_data in reviews_data:
                    review_dict = {
                        "book_id": book_data.get("id"),
                        "litres_review_id": str(review_data.get("id", "")),
                        "author_name": review_data.get("author") or review_data.get("userName") or review_data.get("authorName") or "Анонимный читатель",
                        "rating": review_data.get("rating") or review_data.get("score") or review_data.get("stars"),
                        "text": review_data.get("text") or review_data.get("content") or review_data.get("comment") or review_data.get("reviewText"),
                        "date": _parse_date(review_data.get("date") or review_data.get("createdAt") or review_data.get("created_at"))
                    }
                    
                    ReviewRepositorySupabase.create_or_update(review_dict)
                    stats["total_reviews"] += 1
                
                stats["updated_books"] += 1
            
            # Задержка между запросами (не более 1 запроса в секунду)
            time.sleep(1.1)
        
        return {
            "success": True,
            **stats
        }

