"""Скрипт для инициализации базы данных через Supabase Dashboard."""
import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config import Config

def main():
    """Инструкции по инициализации базы данных."""
    print("=" * 70)
    print("Инициализация базы данных")
    print("=" * 70)
    print()
    
    # Проверка конфигурации
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")
        print("Создайте файл .env и заполните переменные окружения")
        return 1
    
    print("📋 Инструкции по созданию таблиц:")
    print()
    print("1. Откройте Supabase Dashboard:")
    print("   https://supabase.com/dashboard")
    print()
    print("2. Выберите ваш проект")
    print()
    print("3. Перейдите в SQL Editor → New query")
    print()
    print("4. Откройте файл sql/create_tables.sql в проекте")
    print()
    print("5. Скопируйте весь SQL код и выполните в SQL Editor")
    print()
    print("6. Подождите 1-2 минуты для обновления кэша")
    print()
    print("✅ После создания таблиц вы можете добавить книги:")
    print("   python scripts/add_books_from_files.py")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
