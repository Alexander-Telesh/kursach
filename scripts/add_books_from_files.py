"""Скрипт для автоматического добавления книг из папки books/."""
import sys
import os
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.repository_supabase import BookRepositorySupabase
from services.fb2_parser import FB2Parser
from utils.config import Config

# Информация о книгах серии Стеллар
STELLAR_BOOKS_INFO = {
    "0_Arhiv-Stellara.fb2": {
        "title": "Архив Стеллара",
        "author": "Александр Зорич",
        "series_order": 0,
        "description": "Архив серии Стеллар"
    },
    "1. Инкарнатор.fb2": {
        "title": "Инкарнатор",
        "author": "Александр Зорич",
        "series_order": 1,
        "description": "Первая книга серии Стеллар"
    },
    "2. Трибут.fb2": {
        "title": "Трибут",
        "author": "Александр Зорич",
        "series_order": 2,
        "description": "Вторая книга серии Стеллар"
    },
    "3. Заклинатель.fb2": {
        "title": "Заклинатель",
        "author": "Александр Зорич",
        "series_order": 3,
        "description": "Третья книга серии Стеллар"
    },
    "4. Мятежник.fb2": {
        "title": "Мятежник",
        "author": "Александр Зорич",
        "series_order": 4,
        "description": "Четвертая книга серии Стеллар"
    },
    "5. Архонт.fb2": {
        "title": "Архонт",
        "author": "Александр Зорич",
        "series_order": 5,
        "description": "Пятая книга серии Стеллар"
    },
    "6. Легат.fb2": {
        "title": "Легат",
        "author": "Александр Зорич",
        "series_order": 6,
        "description": "Шестая книга серии Стеллар"
    },
    "7. Эфемер.fb2": {
        "title": "Эфемер",
        "author": "Александр Зорич",
        "series_order": 7,
        "description": "Седьмая книга серии Стеллар"
    },
    "8. Сфирот.fb2": {
        "title": "Сфирот",
        "author": "Александр Зорич",
        "series_order": 8,
        "description": "Восьмая книга серии Стеллар"
    },
    "9. Прометей.fb2": {
        "title": "Прометей",
        "author": "Александр Зорич",
        "series_order": 9,
        "description": "Девятая книга серии Стеллар"
    },
}

def get_book_info_from_fb2(file_path):
    """Получить информацию о книге из FB2 файла."""
    parsed = FB2Parser.parse_fb2(file_path)
    if "error" not in parsed:
        return {
            "title": parsed.get("title", ""),
            "author": parsed.get("author", ""),
            "description": parsed.get("description", "")
        }
    return None

def main():
    """Основная функция добавления книг."""
    print("=" * 50)
    print("Добавление книг из папки books/")
    print("=" * 50)
    print()
    
    # Проверка конфигурации
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return 1
    
    # Проверяем папку с книгами
    books_dir = Config.BOOKS_DIR
    if not os.path.exists(books_dir):
        print(f"❌ Папка {books_dir} не найдена")
        return 1
    
    print(f"📁 Папка с книгами: {books_dir}")
    print()
    
    # Получаем список FB2 файлов
    fb2_files = [f for f in os.listdir(books_dir) if f.lower().endswith('.fb2')]
    
    if not fb2_files:
        print("❌ FB2 файлы не найдены в папке books/")
        return 1
    
    print(f"Найдено FB2 файлов: {len(fb2_files)}")
    print()
    
    added_count = 0
    updated_count = 0
    skipped_count = 0
    
    for filename in sorted(fb2_files):
        file_path = os.path.join(books_dir, filename)
        relative_path = f"books/{filename}"
        
        print(f"📖 Обработка: {filename}")
        
        # Проверяем, существует ли книга
        existing_book = None
        # Пробуем найти по пути
        books_data = BookRepositorySupabase.get_all()
        for book_data in books_data:
            if book_data.get("fb2_file_path") == relative_path or book_data.get("fb2_file_path") == file_path:
                existing_book = book_data
                break
        
        # Получаем информацию о книге
        book_info = STELLAR_BOOKS_INFO.get(filename, {})
        
        # Пробуем получить из FB2 файла
        fb2_info = get_book_info_from_fb2(file_path)
        if fb2_info:
            # Объединяем информацию
            title = book_info.get("title") or fb2_info.get("title") or filename.replace(".fb2", "")
            author = book_info.get("author") or fb2_info.get("author") or "Александр Зорич"
            description = book_info.get("description") or fb2_info.get("description") or ""
        else:
            # Используем только из словаря
            title = book_info.get("title", filename.replace(".fb2", ""))
            author = book_info.get("author", "Александр Зорич")
            description = book_info.get("description", "")
        
        if existing_book:
            # Обновляем существующую книгу
            book_update = {
                "title": title,
                "author": author,
                "description": description,
                "series_order": book_info.get("series_order"),
                "fb2_file_path": relative_path
            }
            BookRepositorySupabase.update(existing_book.get("id"), book_update)
            print(f"   ✅ Обновлена: {title}")
            updated_count += 1
        else:
            # Создаем новую книгу
            new_book_data = {
                "title": title,
                "author": author,
                "description": description,
                "series_order": book_info.get("series_order"),
                "fb2_file_path": relative_path
            }
            BookRepositorySupabase.create(new_book_data)
            print(f"   ✅ Добавлена: {title}")
            added_count += 1
    
    print()
    print("=" * 50)
    print("Результаты:")
    print(f"  ✅ Добавлено книг: {added_count}")
    print(f"  🔄 Обновлено книг: {updated_count}")
    print(f"  ⏭️  Пропущено: {skipped_count}")
    print("=" * 50)
    print()
    print("Теперь вы можете запустить приложение:")
    print("  streamlit run app.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())



