"""Вспомогательные функции для работы с данными из Supabase SDK."""
from typing import Dict, List, Optional


class Book:
    """Класс-обертка для работы с книгой из Supabase SDK."""
    
    def __init__(self, data: Dict):
        self.id = data.get("id")
        self.title = data.get("title", "")
        self.author = data.get("author", "")
        self.description = data.get("description")
        self.series_order = data.get("series_order")
        self.fb2_file_path = data.get("fb2_file_path")
        self.litres_book_id = data.get("litres_book_id")
        self.fantlab_work_id = data.get("fantlab_work_id")
        self.fantlab_series_id = data.get("fantlab_series_id")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
        self._data = data
    
    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', author='{self.author}')>"
    
    def to_dict(self) -> Dict:
        """Преобразовать в словарь."""
        return self._data


class Review:
    """Класс-обертка для работы с отзывом/комментарием из Supabase SDK."""
    
    def __init__(self, data: Dict):
        self.id = data.get("id")
        self.book_id = data.get("book_id")
        self.litres_review_id = data.get("litres_review_id")
        self.author_name = data.get("author_name")
        self.likes_count = data.get("likes_count", 0)
        self.comment_type = data.get("comment_type", "comment")
        self.text = data.get("text")
        self.date = data.get("date")
        self.parent_comment_id = data.get("parent_comment_id")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
        self._data = data
    
    def __repr__(self):
        return f"<Review(id={self.id}, book_id={self.book_id}, type={self.comment_type}, likes={self.likes_count})>"
    
    def to_dict(self) -> Dict:
        """Преобразовать в словарь."""
        return self._data


def dict_to_book(data: Dict) -> Book:
    """Преобразовать словарь в объект Book."""
    return Book(data)


def dict_to_review(data: Dict) -> Review:
    """Преобразовать словарь в объект Review."""
    return Review(data)


def dicts_to_books(data_list: List[Dict]) -> List[Book]:
    """Преобразовать список словарей в список объектов Book."""
    return [Book(item) for item in data_list]


def dicts_to_reviews(data_list: List[Dict]) -> List[Review]:
    """Преобразовать список словарей в список объектов Review."""
    return [Review(item) for item in data_list]

