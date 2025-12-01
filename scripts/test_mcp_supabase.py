"""Скрипт для проверки работы Supabase через SDK (аналогично MCP)."""
import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config import Config
from database.supabase_client import get_supabase_client


def test_supabase_sdk():
    """Тестирование подключения к Supabase через SDK."""
    print("=" * 70)
    print("Проверка работы Supabase через Python SDK")
    print("(Аналогично тому, как работает MCP Supabase)")
    print("=" * 70)
    print()
    
    # Проверка конфигурации
    print("1. Проверка конфигурации...")
    try:
        Config.validate()
        print("   ✅ Конфигурация загружена")
        print(f"   SUPABASE_URL: {Config.SUPABASE_URL[:40]}..." if Config.SUPABASE_URL else "   ❌ Не установлен")
        print(f"   SUPABASE_KEY: {'установлен' if Config.SUPABASE_KEY else '❌ не установлен'}")
    except ValueError as e:
        print(f"   ❌ Ошибка: {e}")
        return 1
    
    print()
    
    # Проверка подключения через SDK
    print("2. Подключение к Supabase через SDK...")
    try:
        supabase = get_supabase_client()
        print("   ✅ Клиент Supabase создан успешно")
    except Exception as e:
        print(f"   ❌ Ошибка создания клиента: {e}")
        return 1
    
    print()
    
    # Проверка таблиц
    print("3. Проверка таблиц в базе данных...")
    try:
        # Пробуем получить список таблиц через запрос к таблице books
        response = supabase.table("books").select("id").limit(1).execute()
        print("   ✅ Таблица 'books' доступна")
        
        # Проверяем таблицу reviews
        response = supabase.table("reviews").select("id").limit(1).execute()
        print("   ✅ Таблица 'reviews' доступна")
        
    except Exception as e:
        print(f"   ⚠️  Ошибка при проверке таблиц: {e}")
        print("   Это может быть нормально, если таблицы еще не созданы")
        print("   Запустите: python scripts/init_database.py")
    
    print()
    
    # Тест чтения данных
    print("4. Тест чтения данных...")
    try:
        response = supabase.table("books").select("*").limit(5).execute()
        books_count = len(response.data) if response.data else 0
        print(f"   ✅ Успешно прочитано записей из таблицы books: {books_count}")
        
        if books_count > 0:
            print(f"   Пример первой книги: {response.data[0].get('title', 'N/A')}")
        
    except Exception as e:
        print(f"   ⚠️  Ошибка при чтении данных: {e}")
    
    print()
    
    # Тест поиска
    print("5. Тест поиска...")
    try:
        response = supabase.table("books").select("*").ilike("title", "%Стеллар%").limit(1).execute()
        if response.data:
            print(f"   ✅ Поиск работает. Найдено: {len(response.data)} записей")
        else:
            print("   ℹ️  Поиск работает, но ничего не найдено (это нормально, если база пустая)")
    except Exception as e:
        print(f"   ⚠️  Ошибка при поиске: {e}")
    
    print()
    print("=" * 70)
    print("✅ Проверка завершена!")
    print("=" * 70)
    print()
    print("Если все проверки прошли успешно, MCP Supabase должен работать аналогично.")
    print("Для использования MCP в Cursor:")
    print("1. Убедитесь, что файл .cursor/mcp.json создан и заполнен")
    print("2. Перезапустите Cursor")
    print("3. MCP Supabase будет доступен через ИИ-ассистента")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(test_supabase_sdk())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


