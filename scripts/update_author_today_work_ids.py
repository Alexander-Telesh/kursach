"""Скрипт для добавления author_today_work_id к существующим книгам."""
import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.repository_supabase import BookRepositorySupabase
from utils.config import Config

# Маппинг: порядок книг в базе данных → work_id из AuthorToday
# Ссылки предоставлены пользователем в порядке книг в базе
AUTHORTODAY_WORK_IDS = {
    1: 79155,   # Архив Стеллара
    2: 42665,   # Инкарнатор
    3: 43990,   # Трибут
    4: 56156,   # Заклинатель
    5: 71619,   # Мятежник
    6: 91026,   # Архонт
    7: 110845,  # Легат
    8: 129935,  # Эфемер
    9: 150836,  # Сфирот
    10: 179981, # Прометей
}


def update_work_ids():
    """Обновить author_today_work_id для всех книг."""
    print("=" * 70)
    print("Обновление author_today_work_id для книг")
    print("=" * 70)
    print()
    
    # Проверка конфигурации
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return 1
    
    # Получаем все книги
    print("📚 Получение списка книг...")
    books_data = BookRepositorySupabase.get_all()
    
    if not books_data:
        print("⚠️  В базе данных нет книг")
        return 0
    
    print(f"   Найдено книг: {len(books_data)}")
    print()
    
    # Показываем текущее состояние
    print("📋 Текущее состояние:")
    for book in books_data:
        book_id = book.get("id")
        series_order = book.get("series_order")
        title = book.get("title", "Без названия")
        current_work_id = book.get("author_today_work_id")
        expected_work_id = AUTHORTODAY_WORK_IDS.get(series_order) if series_order else None
        
        status = "✅" if current_work_id == expected_work_id else "⚠️"
        print(f"   {status} #{series_order}: {title}")
        print(f"      Текущий work_id: {current_work_id or 'не установлен'}")
        if expected_work_id:
            print(f"      Ожидаемый work_id: {expected_work_id}")
    print()
    
    # Подтверждение
    print(f"⚠️  ВНИМАНИЕ: Будет обновлено author_today_work_id для {len(books_data)} книг")
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv
    
    if not auto_confirm:
        response = input("Продолжить? (yes/no): ").strip().lower()
        if response not in ['yes', 'y', 'да', 'д']:
            print("❌ Операция отменена")
            return 0
    else:
        print("🔄 Автоматическое обновление...")
    
    print()
    print("🔄 Обновление work_id...")
    
    updated_count = 0
    skipped_count = 0
    failed_count = 0
    
    for book in books_data:
        book_id = book.get("id")
        series_order = book.get("series_order")
        title = book.get("title", "Без названия")
        expected_work_id = AUTHORTODAY_WORK_IDS.get(series_order) if series_order else None
        
        if not expected_work_id:
            print(f"   ⏭️  [{series_order}] '{title}' - нет маппинга для series_order")
            skipped_count += 1
            continue
        
        current_work_id = book.get("author_today_work_id")
        if current_work_id == expected_work_id:
            print(f"   ✅ [{series_order}] '{title}' - уже установлен ({current_work_id})")
            skipped_count += 1
            continue
        
        try:
            BookRepositorySupabase.update(book_id, {"author_today_work_id": expected_work_id})
            print(f"   ✅ [{series_order}] '{title}' - обновлен: {current_work_id or 'не установлен'} → {expected_work_id}")
            updated_count += 1
        except Exception as e:
            print(f"   ❌ [{series_order}] '{title}' - ошибка: {e}")
            failed_count += 1
    
    print()
    print("=" * 70)
    print("Результаты:")
    print(f"  ✅ Обновлено книг: {updated_count}")
    print(f"  ⏭️  Пропущено: {skipped_count}")
    if failed_count > 0:
        print(f"  ❌ Ошибок: {failed_count}")
    print("=" * 70)
    print()
    
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(update_work_ids())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

