"""Скрипт для установки fantlab_work_id и fantlab_series_id для книг серии Стеллар."""
import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.repository_supabase import BookRepositorySupabase

# ID цикла "Стеллар" на FantLab
FANTLAB_SERIES_ID = 1597163

# Маппинг названий книг на их work_id на FantLab
# Заполните правильные ID для каждой книги с сайта fantlab.ru
BOOK_WORK_IDS = {
    "Архив Стеллара": 1597211,
    "Инкарнатор": 1487580,
    "Трибут": 1487580,
    "Заклинатель": 1597165,
    "Мятежник": 1597167,
    "Архонт": 1597169,
    "Легат": 1597175,
    "Эфемер": 1597176,
    "Сфирот": 1597178,
    "Прометей": 1597181,
}

def main():
    """Установить fantlab_work_id и fantlab_series_id для всех книг."""
    print("=" * 70)
    print("Установка FantLab ID для книг серии Стеллар")
    print("=" * 70)
    print()
    
    # Получаем все книги
    books = BookRepositorySupabase.get_all()
    
    if not books:
        print("❌ Книги не найдены в базе данных")
        return 1
    
    print(f"📚 Найдено книг: {len(books)}")
    print()
    
    updated_count = 0
    skipped_count = 0
    
    for book in books:
        book_id = book.get("id")
        book_title = book.get("title", "Без названия")
        current_work_id = book.get("fantlab_work_id")
        current_series_id = book.get("fantlab_series_id")
        
        # Определяем work_id для книги
        work_id = BOOK_WORK_IDS.get(book_title)
        
        # Если ID не найден в маппинге, пропускаем
        if work_id is None:
            print(f"⏭️  Пропущена: '{book_title}' (ID не указан в маппинге)")
            skipped_count += 1
            continue
        
        # Подготавливаем данные для обновления
        update_data = {}
        
        # Устанавливаем work_id, если его еще нет
        if not current_work_id:
            update_data["fantlab_work_id"] = work_id
            print(f"📖 '{book_title}': устанавливаем work_id = {work_id}")
        elif current_work_id != work_id:
            update_data["fantlab_work_id"] = work_id
            print(f"📖 '{book_title}': обновляем work_id {current_work_id} → {work_id}")
        else:
            print(f"✓ '{book_title}': work_id уже установлен ({current_work_id})")
        
        # Устанавливаем series_id, если его еще нет
        if not current_series_id:
            update_data["fantlab_series_id"] = FANTLAB_SERIES_ID
            print(f"   Устанавливаем series_id = {FANTLAB_SERIES_ID}")
        elif current_series_id != FANTLAB_SERIES_ID:
            update_data["fantlab_series_id"] = FANTLAB_SERIES_ID
            print(f"   Обновляем series_id {current_series_id} → {FANTLAB_SERIES_ID}")
        
        # Обновляем в базе данных
        if update_data:
            try:
                BookRepositorySupabase.update(book_id, update_data)
                print(f"   ✅ Обновлено")
                updated_count += 1
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
        else:
            print(f"   ✓ Данные уже актуальны")
            updated_count += 1
        
        print()
    
    print("=" * 70)
    print("Результаты:")
    print(f"  ✅ Обработано: {updated_count}")
    print(f"  ⏭️  Пропущено: {skipped_count}")
    print("=" * 70)
    print()
    print("💡 После установки ID запустите:")
    print("   python scripts/update_fantlab_data.py")
    print("   для обновления данных с FantLab")
    
    return 0

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

