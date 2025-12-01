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
        supabase_url = Config.SUPABASE_URL
        supabase_key = Config.SUPABASE_KEY
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL и SUPABASE_KEY должны быть установлены в .env файле или Streamlit secrets"
            )
        
        _supabase_client = create_client(supabase_url, supabase_key)
    
    return _supabase_client


def reset_supabase_client():
    """Сбросить клиент Supabase (для тестирования)."""
    global _supabase_client
    _supabase_client = None



