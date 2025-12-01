"""Модуль для работы с базой данных через Supabase SDK."""
from .repository_supabase import BookRepositorySupabase, ReviewRepositorySupabase
from .supabase_client import get_supabase_client
from .helpers import Book, Review, dict_to_book, dict_to_review, dicts_to_books, dicts_to_reviews

__all__ = [
    "BookRepositorySupabase", 
    "ReviewRepositorySupabase",
    "get_supabase_client",
    "Book",
    "Review",
    "dict_to_book",
    "dict_to_review",
    "dicts_to_books",
    "dicts_to_reviews"
]





