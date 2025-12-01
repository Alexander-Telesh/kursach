"""Клиент Supabase для работы через REST API."""
from supabase import create_client, Client
from utils.config import Config
from typing import Optional

# Глобальный клиент Supabase
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Получить клиент Supabase.
    
    Returns:
        Клиент Supabase для работы через REST API
    """
    global _supabase_client
    
    if _supabase_client is None:
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            raise ValueError(
                "SUPABASE_URL и SUPABASE_KEY должны быть установлены в .env файле"
            )
        
        _supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    return _supabase_client


def reset_supabase_client():
    """Сбросить клиент Supabase (для тестирования)."""
    global _supabase_client
    _supabase_client = None



