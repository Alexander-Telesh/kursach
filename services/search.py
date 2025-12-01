"""Модуль для текстового поиска."""
from database.repository_supabase import BookRepositorySupabase
from typing import List, Dict


def search_books(query: str, use_full_text: bool = True) -> List[Dict]:
    """
    Поиск книг по запросу.
    
    Args:
        query: Поисковый запрос
        use_full_text: Использовать полнотекстовый поиск PostgreSQL
    
    Returns:
        Список найденных книг (словари)
    """
    if not query or not query.strip():
        return BookRepositorySupabase.get_all()
    
    query = query.strip()
    
    if use_full_text:
        return BookRepositorySupabase.full_text_search(query)
    else:
        return BookRepositorySupabase.search(query)
