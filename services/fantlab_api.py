"""Интеграция с FantLab.ru API для получения оценок, отзывов и аннотаций."""
import requests
import time
from typing import List, Dict, Optional
from datetime import datetime
from utils.config import Config


class FantLab:
    """Класс для работы с FantLab.ru API."""
    
    def __init__(self):
        self.api_url = Config.FANTLAB_API_URL or "https://api.fantlab.ru"
        self.web_url = Config.FANTLAB_WEB_URL or "https://fantlab.ru"
        self.api_key = Config.FANTLAB_API_KEY or ""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Выполнить запрос к API FantLab.
        
        Args:
            endpoint: Эндпоинт API (например, "/work/123")
            params: Параметры запроса
        
        Returns:
            JSON ответ или None при ошибке
        """
        try:
            url = f"{self.api_url}{endpoint}"
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"   ⚠️  Ресурс не найден: {endpoint}")
                return None
            else:
                print(f"   ⚠️  Ошибка API {response.status_code}: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"   ❌ Ошибка запроса к FantLab API: {e}")
            return None
    
    def get_work_info(self, work_id: int) -> Dict:
        """
        Получить информацию о произведении.
        
        Args:
            work_id: ID произведения на FantLab
        
        Returns:
            Словарь с информацией: annotation, rating, reviews_count, etc.
        """
        data = self._make_request(f"/work/{work_id}")
        
        if not data:
            return {"error": "Не удалось получить данные"}
        
        result = {
            "annotation": data.get("annotation") or data.get("description") or "",
            "rating": data.get("rating") or data.get("average_rating") or 0.0,
            "reviews_count": data.get("reviews_count") or data.get("reviews") or 0,
            "title": data.get("title") or data.get("name") or "",
            "author": data.get("author") or data.get("author_name") or ""
        }
        
        return result
    
    def get_work_rating(self, work_id: int) -> float:
        """
        Получить среднюю оценку произведения.
        
        Args:
            work_id: ID произведения на FantLab
        
        Returns:
            Средняя оценка (0.0 - 10.0) или 0.0 при ошибке
        """
        data = self._make_request(f"/work/{work_id}")
        
        if not data:
            return 0.0
        
        rating = data.get("rating") or data.get("average_rating") or data.get("score") or 0.0
        return float(rating)
    
    def get_work_reviews(self, work_id: int, page: int = 1, limit: int = 100) -> List[Dict]:
        """
        Получить отзывы на произведение.
        
        Args:
            work_id: ID произведения на FantLab
            page: Номер страницы
            limit: Количество отзывов на странице
        
        Returns:
            Список отзывов: id, author_name, text, date, rating, likes_count
        """
        params = {"page": page, "limit": limit}
        data = self._make_request(f"/work/{work_id}/reviews", params=params)
        
        if not data:
            return []
        
        reviews = []
        
        # Обрабатываем разные форматы ответа
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("reviews") or data.get("items") or data.get("data") or []
        
        for item in items:
            try:
                review = {
                    "id": str(item.get("id") or item.get("review_id") or ""),
                    "author_name": item.get("author") or item.get("author_name") or item.get("user") or "Анонимный читатель",
                    "text": item.get("text") or item.get("content") or item.get("review_text") or "",
                    "date": item.get("date") or item.get("created_at") or item.get("created"),
                    "rating": float(item.get("rating") or item.get("score") or 0),
                    "likes_count": int(item.get("likes") or item.get("likes_count") or 0)
                }
                
                if review["text"] and len(review["text"].strip()) > 0:
                    reviews.append(review)
            except Exception as e:
                continue
        
        return reviews
    
    def get_series_info(self, series_id: int) -> Dict:
        """
        Получить информацию о цикле/серии.
        
        Args:
            series_id: ID цикла на FantLab
        
        Returns:
            Словарь с информацией: annotation, rating, reviews_count, works
        """
        data = self._make_request(f"/cycle/{series_id}")
        
        if not data:
            return {"error": "Не удалось получить данные"}
        
        result = {
            "annotation": data.get("annotation") or data.get("description") or "",
            "rating": data.get("rating") or data.get("average_rating") or 0.0,
            "reviews_count": data.get("reviews_count") or data.get("reviews") or 0,
            "title": data.get("title") or data.get("name") or "",
            "works": data.get("works") or data.get("books") or []
        }
        
        return result
    
    def get_series_rating(self, series_id: int) -> float:
        """
        Получить среднюю оценку цикла.
        
        Args:
            series_id: ID цикла на FantLab
        
        Returns:
            Средняя оценка (0.0 - 10.0) или 0.0 при ошибке
        """
        data = self._make_request(f"/cycle/{series_id}")
        
        if not data:
            return 0.0
        
        rating = data.get("rating") or data.get("average_rating") or data.get("score") or 0.0
        return float(rating)
    
    def get_series_reviews(self, series_id: int, page: int = 1, limit: int = 100) -> List[Dict]:
        """
        Получить отзывы на цикл.
        
        Args:
            series_id: ID цикла на FantLab
            page: Номер страницы
            limit: Количество отзывов на странице
        
        Returns:
            Список отзывов: id, author_name, text, date, rating, likes_count
        """
        params = {"page": page, "limit": limit}
        data = self._make_request(f"/cycle/{series_id}/reviews", params=params)
        
        if not data:
            return []
        
        reviews = []
        
        # Обрабатываем разные форматы ответа
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("reviews") or data.get("items") or data.get("data") or []
        
        for item in items:
            try:
                review = {
                    "id": str(item.get("id") or item.get("review_id") or ""),
                    "author_name": item.get("author") or item.get("author_name") or item.get("user") or "Анонимный читатель",
                    "text": item.get("text") or item.get("content") or item.get("review_text") or "",
                    "date": item.get("date") or item.get("created_at") or item.get("created"),
                    "rating": float(item.get("rating") or item.get("score") or 0),
                    "likes_count": int(item.get("likes") or item.get("likes_count") or 0)
                }
                
                if review["text"] and len(review["text"].strip()) > 0:
                    reviews.append(review)
            except Exception as e:
                continue
        
        return reviews


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Парсинг даты из различных форматов."""
    if not date_str:
        return None
    
    try:
        if "T" in str(date_str):
            return datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        # Другие форматы можно добавить при необходимости
    except:
        pass
    
    return None


def sync_reviews_from_fantlab(book_id: Optional[int] = None, update_ratings_only: bool = False) -> Dict:
    """
    Синхронизировать отзывы и оценки с FantLab.
    
    Args:
        book_id: ID книги (если None, обновляются все книги)
        update_ratings_only: Если True, обновляются только оценки существующих записей
    
    Returns:
        Словарь со статистикой обновления
    """
    from database.repository_supabase import BookRepositorySupabase, ReviewRepositorySupabase
    
    api = FantLab()
    
    def process_book(book_data: Dict) -> Dict:
        """Обработать одну книгу."""
        book_id = book_data.get("id")
        book_title = book_data.get("title", "")
        work_id = book_data.get("fantlab_work_id")
        series_id = book_data.get("fantlab_series_id")
        
        stats = {
            "book_id": book_id,
            "reviews": 0,
            "rating": 0.0,
            "error": None
        }
        
        if not work_id:
            stats["error"] = "fantlab_work_id не установлен"
            return stats
        
        print(f"📖 Обработка: '{book_title}' (work_id: {work_id})")
        
        try:
            # Получаем информацию о произведении
            work_info = api.get_work_info(work_id)
            
            if "error" not in work_info:
                stats["rating"] = work_info.get("rating", 0.0)
            
            if not update_ratings_only:
                # Получаем отзывы на произведение
                reviews = api.get_work_reviews(work_id)
                print(f"   📄 Найдено отзывов: {len(reviews)}")
                
                for review_data in reviews:
                    review_dict = {
                        "book_id": book_id,
                        "litres_review_id": str(review_data.get("id", "")),
                        "comment_type": "review",
                        "author_name": review_data.get("author_name", "Анонимный читатель"),
                        "text": review_data.get("text", ""),
                        "likes_count": int(review_data.get("likes_count", 0)),
                        "date": _parse_date(review_data.get("date"))
                    }
                    
                    if review_dict["text"] and len(review_dict["text"].strip()) > 0:
                        try:
                            ReviewRepositorySupabase.create_or_update(review_dict)
                            stats["reviews"] += 1
                        except Exception as e:
                            print(f"   ⚠️  Ошибка при сохранении отзыва: {e}")
            
            time.sleep(0.5)  # Задержка между запросами
            
        except Exception as e:
            stats["error"] = str(e)
            print(f"   ❌ Ошибка обработки книги: {e}")
        
        return stats
    
    def process_series(series_id: int) -> Dict:
        """Обработать цикл (получить отзывы на цикл)."""
        stats = {
            "series_id": series_id,
            "reviews": 0,
            "rating": 0.0
        }
        
        try:
            series_info = api.get_series_info(series_id)
            
            if "error" not in series_info:
                stats["rating"] = series_info.get("rating", 0.0)
            
            if not update_ratings_only:
                reviews = api.get_series_reviews(series_id)
                print(f"📚 Отзывов на цикл: {len(reviews)}")
                
                # Сохраняем отзывы на цикл
                # Для простоты сохраняем их с book_id первой книги цикла
                books_data = BookRepositorySupabase.get_all()
                first_book_id = books_data[0].get("id") if books_data else None
                
                for review_data in reviews:
                    review_dict = {
                        "book_id": first_book_id,  # Привязываем к первой книге
                        "litres_review_id": f"series_{series_id}_{review_data.get('id', '')}",
                        "comment_type": "review",
                        "author_name": review_data.get("author_name", "Анонимный читатель"),
                        "text": review_data.get("text", ""),
                        "likes_count": int(review_data.get("likes_count", 0)),
                        "date": _parse_date(review_data.get("date"))
                    }
                    
                    if review_dict["text"] and len(review_dict["text"].strip()) > 0:
                        try:
                            ReviewRepositorySupabase.create_or_update(review_dict)
                            stats["reviews"] += 1
                        except Exception as e:
                            print(f"   ⚠️  Ошибка при сохранении отзыва на цикл: {e}")
            
        except Exception as e:
            print(f"❌ Ошибка обработки цикла: {e}")
        
        return stats
    
    if book_id:
        book_data = BookRepositorySupabase.get_by_id(book_id)
        if not book_data:
            return {"success": False, "error": "Книга не найдена"}
        
        stats = process_book(book_data)
        return {"success": True, "book_id": book_id, **stats}
    else:
        books_data = BookRepositorySupabase.get_all()
        total_stats = {
            "total_books": len(books_data),
            "updated_books": 0,
            "total_reviews": 0,
            "total_rating": 0.0
        }
        
        # Обрабатываем цикл (если есть series_id у первой книги)
        if books_data:
            first_book = books_data[0]
            series_id = first_book.get("fantlab_series_id")
            if series_id:
                series_stats = process_series(series_id)
                total_stats["series_rating"] = series_stats.get("rating", 0.0)
                total_stats["series_reviews"] = series_stats.get("reviews", 0)
        
        for book_data in books_data:
            stats = process_book(book_data)
            
            if stats.get("reviews", 0) > 0 or stats.get("rating", 0) > 0:
                total_stats["updated_books"] += 1
            
            total_stats["total_reviews"] += stats.get("reviews", 0)
            total_stats["total_rating"] += stats.get("rating", 0.0)
            
            time.sleep(1)
        
        return {"success": True, **total_stats}

