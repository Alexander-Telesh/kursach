"""Конфигурация приложения и загрузка переменных окружения."""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла (для локальной разработки)
load_dotenv()


def _get_config_value(key: str, default: str = "") -> str:
    """
    Получить значение конфигурации из Streamlit secrets или переменных окружения.
    
    Приоритет:
    1. Streamlit secrets (для Streamlit Cloud)
    2. Переменные окружения (для локальной разработки)
    3. Значение по умолчанию
    """
    # Пробуем получить из Streamlit secrets (для Streamlit Cloud)
    try:
        import streamlit as st
        # Проверяем, что Streamlit инициализирован (не в скрипте)
        if hasattr(st, 'secrets'):
            try:
                # Вариант 1: st.secrets[key] (прямой доступ)
                value = st.secrets[key]
                if value:
                    return str(value)
            except (KeyError, TypeError, AttributeError):
                try:
                    # Вариант 2: st.secrets.secrets[key] (для secrets.toml)
                    if hasattr(st.secrets, 'secrets'):
                        value = st.secrets.secrets[key]
                        if value:
                            return str(value)
                except (KeyError, AttributeError):
                    pass
            except Exception:
                # Игнорируем ошибки Streamlit secrets (например, когда не инициализирован)
                pass
    except (ImportError, RuntimeError, AttributeError):
        # Streamlit не доступен или не инициализирован
        pass
    except Exception:
        # Игнорируем любые другие ошибки при работе с Streamlit
        pass
    
    # Fallback на переменные окружения
    return os.getenv(key, default)


class ConfigMeta(type):
    """Метакласс для динамической загрузки значений конфигурации."""
    
    def __getattr__(cls, name: str):
        """Динамическая загрузка значений конфигурации."""
        # Маппинг имен на ключи и значения по умолчанию
        config_map = {
            'SUPABASE_URL': ('SUPABASE_URL', ''),
            'SUPABASE_KEY': ('SUPABASE_KEY', ''),
            'SUPABASE_DB_URL': ('SUPABASE_DB_URL', ''),
            'AUTHORTODAY_API_URL': ('AUTHORTODAY_API_URL', 'https://api.author.today'),
            'AUTHORTODAY_WEB_URL': ('AUTHORTODAY_WEB_URL', 'https://author.today'),
            'AUTHORTODAY_LOGIN': ('AUTHORTODAY_LOGIN', ''),
            'AUTHORTODAY_PASSWORD': ('AUTHORTODAY_PASSWORD', ''),
            'AUTHORTODAY_TOKEN': ('AUTHORTODAY_TOKEN', ''),
        }
        
        if name in config_map:
            key, default = config_map[name]
            return _get_config_value(key, default)
        
        raise AttributeError(f"'{cls.__name__}' object has no attribute '{name}'")


class Config(metaclass=ConfigMeta):
    """Класс для хранения конфигурации приложения."""
    
    # Путь к папке с книгами (статический)
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
