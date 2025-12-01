"""Скрипт для добавления fantlab_work_id и fantlab_series_id к существующим книгам."""
import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.repository_supabase import BookRepositorySupabase
from utils.config import Config

# Маппинг: порядок книг в базе данных → work_id из FantLab
# Series ID: 1597163 (цикл "Стеллар")
FANTLAB_SERIES_ID = 1597163

# Work IDs в порядке series_order
FANTLAB_WORK_IDS = {
    1: 1597211,   # Книга 1
    2: 1487580,   # Книга 2
    3: 1597165,   # Книга 3
    4: 1597167,   # Книга 4
    5: 1597169,   # Книга 5
    6: 1597173,   # Книга 6
    7: 1597175,   # Книга 7
    8: 1597176,   # Книга 8
    9: 1597178,   # Книга 9
    10: 1597181,  # Книга 10
}


def update_fantlab_ids(dry_run: bool = True):
    """Обновить fantlab_work_id и fantlab_series_id для всех книг."""
    
    if dry_run:
        print("🔍 РЕЖИМ ПРОВЕРКИ (dry-run) - изменения не будут сохранены")
    else:
        print("⚠️  РЕЖИМ ОБНОВЛЕНИЯ - изменения будут сохранены в базе данных")
    
    print("Обновление fantlab_work_id и fantlab_series_id для книг")
    print("=" * 70)
    
    books_data = BookRepositorySupabase.get_all()
    
    if not books_data:
        print("❌ Книги не найдены в базе данных")
        return
    
    print(f"Найдено книг: {len(books_data)}")
    print()
    
    updates = []
    
    for book in books_data:
        book_id = book.get("id")
        title = book.get("title", "Без названия")
        series_order = book.get("series_order")
        
        current_work_id = book.get("fantlab_work_id")
        current_series_id = book.get("fantlab_series_id")
        
        expected_work_id = FANTLAB_WORK_IDS.get(series_order) if series_order else None
        expected_series_id = FANTLAB_SERIES_ID
        
        if expected_work_id:
            if current_work_id != expected_work_id or current_series_id != expected_series_id:
                updates.append({
                    "book_id": book_id,
                    "title": title,
                    "series_order": series_order,
                    "current_work_id": current_work_id,
                    "current_series_id": current_series_id,
                    "expected_work_id": expected_work_id,
                    "expected_series_id": expected_series_id
                })
    
    if not updates:
        print("✅ Все книги уже имеют правильные fantlab_work_id и fantlab_series_id")
        return
    
    print(f"⚠️  ВНИМАНИЕ: Будет обновлено fantlab_work_id и fantlab_series_id для {len(updates)} книг")
    print()
    print("Список изменений:")
    print("-" * 70)
    
    for update in updates:
        print(f"Книга #{update['series_order']}: {update['title']}")
        print(f"  Текущий work_id: {update['current_work_id'] or 'НЕТ'} → Новый: {update['expected_work_id']}")
        print(f"  Текущий series_id: {update['current_series_id'] or 'НЕТ'} → Новый: {update['expected_series_id']}")
        print()
    
    if dry_run:
        print("=" * 70)
        print("Это был режим проверки. Для применения изменений запустите:")
        print("  python scripts/migrate_to_fantlab.py --apply")
        return
    
    # Применяем изменения
    print("=" * 70)
    print("Применение изменений...")
    
    for update in updates:
        book_id = update["book_id"]
        expected_work_id = update["expected_work_id"]
        expected_series_id = update["expected_series_id"]
        
        try:
            BookRepositorySupabase.update(book_id, {
                "fantlab_work_id": expected_work_id,
                "fantlab_series_id": expected_series_id
            })
            print(f"✅ Обновлена книга #{update['series_order']}: {update['title']}")
        except Exception as e:
            print(f"❌ Ошибка при обновлении книги #{update['series_order']}: {e}")
    
    print()
    print("=" * 70)
    print("✅ Обновление завершено")


if __name__ == "__main__":
    dry_run = "--apply" not in sys.argv
    
    try:
        update_fantlab_ids(dry_run=dry_run)
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

