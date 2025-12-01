"""Конфигурация приложения и загрузка переменных окружения."""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


class Config:
    """Класс для хранения конфигурации приложения."""
    
    # Supabase настройки
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL", "")
    
    # AuthorToday API настройки
    AUTHORTODAY_API_URL = os.getenv("AUTHORTODAY_API_URL", "https://api.author.today")
    AUTHORTODAY_WEB_URL = os.getenv("AUTHORTODAY_WEB_URL", "https://author.today")
    AUTHORTODAY_LOGIN = os.getenv("AUTHORTODAY_LOGIN", "")  # Логин для авторизации
    AUTHORTODAY_PASSWORD = os.getenv("AUTHORTODAY_PASSWORD", "")  # Пароль для авторизации
    AUTHORTODAY_TOKEN = os.getenv("AUTHORTODAY_TOKEN", "")  # Токен (опционально, получается при авторизации)
    
    # Путь к папке с книгами
    BOOKS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "books")
    
    @classmethod
    def validate(cls):
        """Проверка наличия обязательных переменных окружения."""
        required_vars = {
            "SUPABASE_URL": cls.SUPABASE_URL,
            "SUPABASE_KEY": cls.SUPABASE_KEY,
            "SUPABASE_DB_URL": cls.SUPABASE_DB_URL,
        }
        
        missing = [key for key, value in required_vars.items() if not value]
        if missing:
            raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing)}")
        
        return True



