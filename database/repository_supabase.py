"""Репозитории для работы с данными через Supabase SDK (основной подход)."""
from typing import List, Dict, Optional
from database.supabase_client import get_supabase_client


class BookRepositorySupabase:
    """Репозиторий для работы с книгами через Supabase SDK."""
    
    @staticmethod
    def get_all() -> List[Dict]:
        """Получить все книги."""
        supabase = get_supabase_client()
        response = supabase.table("books").select("*").order("series_order", desc=False).execute()
        return response.data if response.data else []
    
    @staticmethod
    def get_by_id(book_id: int) -> Optional[Dict]:
        """Получить книгу по ID."""
        supabase = get_supabase_client()
        response = supabase.table("books").select("*").eq("id", book_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def get_by_litres_id(litres_id: str) -> Optional[Dict]:
        """Получить книгу по ID из Litres/AuthorToday."""
        supabase = get_supabase_client()
        response = supabase.table("books").select("*").eq("litres_book_id", litres_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def search(query: str) -> List[Dict]:
        """Поиск книг по запросу (простой поиск через ilike)."""
        if not query or not query.strip():
            return BookRepositorySupabase.get_all()
        
        supabase = get_supabase_client()
        query_lower = query.lower().strip()
        
        # Используем ilike для поиска (PostgreSQL case-insensitive)
        response = supabase.table("books").select("*").or_(
            f"title.ilike.%{query_lower}%,author.ilike.%{query_lower}%,description.ilike.%{query_lower}%"
        ).execute()
        return response.data if response.data else []
    
    @staticmethod
    def full_text_search(query: str) -> List[Dict]:
        """
        Полнотекстовый поиск через RPC функцию.
        
        Примечание: Требует создания RPC функции в Supabase.
        Если функция не создана, использует простой поиск.
        """
        if not query or not query.strip():
            return BookRepositorySupabase.get_all()
        
        supabase = get_supabase_client()
        query_clean = query.strip()
        
        # Пробуем вызвать RPC функцию для полнотекстового поиска
        try:
            response = supabase.rpc("search_books_fulltext", {"search_query": query_clean}).execute()
            if response.data:
                return response.data
        except Exception:
            pass
        
        # Fallback на простой поиск
        return BookRepositorySupabase.search(query)
    
    @staticmethod
    def create(book_data: Dict) -> Dict:
        """Создать новую книгу."""
        supabase = get_supabase_client()
        response = supabase.table("books").insert(book_data).execute()
        return response.data[0] if response.data else {}
    
    @staticmethod
    def update(book_id: int, book_data: Dict) -> Dict:
        """Обновить книгу."""
        supabase = get_supabase_client()
        response = supabase.table("books").update(book_data).eq("id", book_id).execute()
        return response.data[0] if response.data else {}
    
    @staticmethod
    def delete(book_id: int) -> bool:
        """Удалить книгу."""
        supabase = get_supabase_client()
        response = supabase.table("books").delete().eq("id", book_id).execute()
        return len(response.data) > 0 if response.data else False


class ReviewRepositorySupabase:
    """Репозиторий для работы с отзывами через Supabase SDK."""
    
    @staticmethod
    def get_by_book_id(book_id: int, comment_type: str = None) -> List[Dict]:
        """Получить все отзывы/комментарии для книги."""
        if comment_type:
            return ReviewRepositorySupabase.get_by_book_id_and_type(book_id, comment_type)
        
        supabase = get_supabase_client()
        try:
            response = supabase.table("reviews").select("*").eq("book_id", book_id).order("date", desc=True).execute()
            data = response.data if response.data else []
            # Сортируем в Python: сначала записи с датой, потом без даты
            data.sort(key=lambda x: (
                x.get("date") is None,  # False (0) для записей с датой, True (1) для без даты
                x.get("date") or "",  # Сортировка по дате
                x.get("id", 0)  # Если дата одинаковая, сортируем по ID
            ), reverse=True)
            return data
        except Exception:
            # Fallback: сортировка по ID
            response = supabase.table("reviews").select("*").eq("book_id", book_id).order("id", desc=True).execute()
            return response.data if response.data else []
    
    @staticmethod
    def get_all_recent(limit: int = 10) -> List[Dict]:
        """Получить последние отзывы."""
        supabase = get_supabase_client()
        try:
            # Получаем больше записей для сортировки в Python
            response = supabase.table("reviews").select("*").order("date", desc=True).limit(limit * 2).execute()
            data = response.data if response.data else []
            # Сортируем в Python: сначала записи с датой, потом без даты
            data.sort(key=lambda x: (
                x.get("date") is None,  # False (0) для записей с датой, True (1) для без даты
                x.get("date") or "",  # Сортировка по дате
                x.get("id", 0)  # Если дата одинаковая, сортируем по ID
            ), reverse=True)
            return data[:limit]
        except Exception:
            # Fallback: сортировка по ID
            response = supabase.table("reviews").select("*").order("id", desc=True).limit(limit).execute()
            return response.data if response.data else []
    
    @staticmethod
    def get_by_book_id_and_type(book_id: int = None, comment_type: str = None) -> List[Dict]:
        """Получить отзывы/комментарии для книги, опционально фильтруя по типу.
        
        Args:
            book_id: ID книги. Если None, возвращает все отзывы.
            comment_type: Тип комментария ('comment' или 'review'). Если None, возвращает все типы.
        """
        supabase = get_supabase_client()
        query = supabase.table("reviews").select("*")
        
        if book_id is not None:
            query = query.eq("book_id", book_id)
        
        if comment_type:
            query = query.eq("comment_type", comment_type)
        
        # Сортируем по дате (новые сначала)
        # Supabase SDK не поддерживает множественные order() или nulls_last
        # Поэтому сортируем только по date, а NULL значения обработаем в Python
        try:
            response = query.order("date", desc=True).execute()
        except Exception:
            # Fallback: сортировка по ID, если сортировка по date не работает
            response = query.order("id", desc=True).execute()
        
        data = response.data if response.data else []
        
        # Сортируем в Python: сначала записи с датой, потом без даты
        data.sort(key=lambda x: (
            x.get("date") is None,  # False (0) для записей с датой, True (1) для без даты
            x.get("date") or "",  # Сортировка по дате
            x.get("id", 0)  # Если дата одинаковая, сортируем по ID
        ), reverse=True)
        
        return data
    
    @staticmethod
    def get_by_book_id_sorted_by_likes(book_id: int, limit: int = None) -> List[Dict]:
        """Получить отзывы/комментарии для книги, отсортированные по количеству лайков."""
        supabase = get_supabase_client()
        query = supabase.table("reviews").select("*").eq("book_id", book_id)
        
        # Supabase SDK не поддерживает nulls_last, поэтому сортируем в Python
        try:
            response = query.order("likes_count", desc=True).execute()
            data = response.data if response.data else []
            # Сортируем в Python: сначала записи с лайками, потом без лайков
            data.sort(key=lambda x: (
                x.get("likes_count") is None,  # False (0) для записей с лайками, True (1) для без лайков
                x.get("likes_count", 0)  # Сортировка по количеству лайков
            ), reverse=True)
            
            if limit:
                return data[:limit]
            return data
        except Exception:
            # Fallback: получаем без сортировки и сортируем в Python
            response = query.execute()
            data = response.data if response.data else []
            data.sort(key=lambda x: x.get("likes_count", 0), reverse=True)
            if limit:
                return data[:limit]
            return data
    
    @staticmethod
    def get_total_likes_for_book(book_id: int) -> int:
        """Получить общее количество лайков для книги."""
        supabase = get_supabase_client()
        response = supabase.table("reviews").select("likes_count").eq("book_id", book_id).execute()
        
        if response.data:
            return sum(r.get("likes_count", 0) for r in response.data)
        return 0
    
    @staticmethod
    def create(review_data: Dict) -> Dict:
        """Создать новый отзыв."""
        supabase = get_supabase_client()
        response = supabase.table("reviews").insert(review_data).execute()
        return response.data[0] if response.data else {}
    
    @staticmethod
    def update(review_id: int, review_data: Dict) -> Dict:
        """Обновить отзыв по ID."""
        supabase = get_supabase_client()
        response = supabase.table("reviews").update(review_data).eq("id", review_id).execute()
        return response.data[0] if response.data else {}
    
    @staticmethod
    def create_or_update(review_data: Dict) -> Dict:
        """Создать или обновить отзыв."""
        supabase = get_supabase_client()
        litres_review_id = review_data.get("litres_review_id")
        
        if litres_review_id:
            # Проверяем существование
            existing = supabase.table("reviews").select("*").eq("litres_review_id", litres_review_id).execute()
            if existing.data:
                # Обновляем
                response = supabase.table("reviews").update(review_data).eq("litres_review_id", litres_review_id).execute()
                return response.data[0] if response.data else {}
        
        # Создаем новый
        return ReviewRepositorySupabase.create(review_data)



