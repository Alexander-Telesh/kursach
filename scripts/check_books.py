"""Скрипт для проверки наличия всех книг серии Стеллар в базе данных."""
import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.repository_supabase import BookRepositorySupabase

# Ожидаемые книги серии Стеллар
EXPECTED_BOOKS = [
    "Архив Стеллара",
    "Инкарнатор",
    "Трибут",
    "Заклинатель",
    "Мятежник",
    "Архонт",
    "Легат",
    "Эфемер",
    "Сфирот",
    "Прометей",
]

def normalize_title(title: str) -> str:
    """Нормализовать название для сравнения."""
    if not title:
        return ""
    return title.strip().lower().replace(" ", "").replace("ё", "е")


def main():
    """Проверить наличие всех книг в базе данных."""
    print("=" * 70)
    print("Проверка наличия книг серии Стеллар в базе данных")
    print("=" * 70)
    print()
    
    # Получаем все книги из базы
    books = BookRepositorySupabase.get_all()
    
    if not books:
        print("❌ Книги не найдены в базе данных")
        return 1
    
    print(f"📚 Всего книг в базе: {len(books)}")
    print()
    
    # Нормализуем названия книг из базы
    books_in_db = {}
    for book in books:
        title = book.get("title", "Без названия")
        normalized = normalize_title(title)
        books_in_db[normalized] = {
            "id": book.get("id"),
            "title": title,
            "work_id": book.get("fantlab_work_id"),
            "series_id": book.get("fantlab_series_id"),
            "file_path": book.get("fb2_file_path"),
        }
    
    # Проверяем наличие каждой ожидаемой книги
    print("📋 Проверка наличия книг:")
    print()
    
    missing_books = []
    found_books = []
    
    for expected_title in EXPECTED_BOOKS:
        normalized_expected = normalize_title(expected_title)
        
        if normalized_expected in books_in_db:
            book_info = books_in_db[normalized_expected]
            found_books.append(expected_title)
            status = "✅"
            work_id_info = f"work_id: {book_info['work_id']}" if book_info['work_id'] else "work_id: не установлен"
            file_info = f"файл: {book_info['file_path']}" if book_info['file_path'] else "файл: не указан"
            print(f"   {status} '{expected_title}' (ID: {book_info['id']}, {work_id_info}, {file_info})")
        else:
            missing_books.append(expected_title)
            print(f"   ❌ '{expected_title}' - ОТСУТСТВУЕТ в базе данных")
    
    print()
    
    # Показываем книги, которые есть в базе, но не в списке ожидаемых
    print("📋 Дополнительные книги в базе (не в списке ожидаемых):")
    found_normalized = {normalize_title(title) for title in found_books}
    extra_books = []
    for normalized, book_info in books_in_db.items():
        if normalized not in found_normalized:
            extra_books.append(book_info['title'])
            print(f"   ⚠️  '{book_info['title']}' (ID: {book_info['id']})")
    
    if not extra_books:
        print("   (нет дополнительных книг)")
    
    print()
    print("=" * 70)
    print("Результаты:")
    print(f"  ✅ Найдено: {len(found_books)}/{len(EXPECTED_BOOKS)}")
    if missing_books:
        print(f"  ❌ Отсутствует: {len(missing_books)}")
        print()
        print("  Отсутствующие книги:")
        for book in missing_books:
            print(f"    - {book}")
    else:
        print("  ✅ Все книги найдены!")
    
    if extra_books:
        print(f"  ⚠️  Дополнительных книг: {len(extra_books)}")
    print("=" * 70)
    print()
    
    if missing_books:
        print("💡 Для добавления отсутствующих книг:")
        print("   1. Убедитесь, что FB2 файл находится в папке books/")
        print("   2. Запустите: python scripts/add_books_from_files.py")
        print("   3. Затем запустите: python scripts/set_fantlab_ids.py")
    
    return 0 if not missing_books else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

