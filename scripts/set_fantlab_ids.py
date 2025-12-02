"""Скрипт для установки fantlab_work_id и fantlab_series_id для книг серии Стеллар."""
import sys
import argparse
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
    "Трибут": 1597165,
    "Заклинатель": 1597167,
    "Мятежник": 1597169,
    "Архонт": 1597173,
    "Легат": 1597175,
    "Эфемер": 1597176,
    "Сфирот": 1597178,
    "Прометей": 1597181,
}

def normalize_title(title: str) -> str:
    """Нормализовать название для сравнения (убрать пробелы, привести к нижнему регистру)."""
    if not title:
        return ""
    return title.strip().lower().replace(" ", "").replace("ё", "е")


def find_work_id(book_title: str) -> tuple:
    """
    Найти work_id для книги по названию.
    Возвращает (work_id, matched_key) или (None, None) если не найдено.
    """
    # Сначала пробуем точное совпадение
    if book_title in BOOK_WORK_IDS:
        return BOOK_WORK_IDS[book_title], book_title
    
    # Нормализуем название книги
    normalized_title = normalize_title(book_title)
    
    # Ищем по нормализованным названиям
    for key, work_id in BOOK_WORK_IDS.items():
        normalized_key = normalize_title(key)
        if normalized_title == normalized_key:
            return work_id, key
    
    # Пробуем частичное совпадение (название книги содержит ключ или наоборот)
    for key, work_id in BOOK_WORK_IDS.items():
        normalized_key = normalize_title(key)
        if normalized_key in normalized_title or normalized_title in normalized_key:
            return work_id, key
    
    return None, None


def main(force_update: bool = False):
    """
    Установить fantlab_work_id и fantlab_series_id для всех книг.
    
    Args:
        force_update: Если True, обновляет значения даже если они уже установлены
    """
    print("=" * 70)
    print("Установка FantLab ID для книг серии Стеллар")
    if force_update:
        print("⚠️  РЕЖИМ ПРИНУДИТЕЛЬНОГО ОБНОВЛЕНИЯ")
    print("=" * 70)
    print()
    
    # Получаем все книги
    books = BookRepositorySupabase.get_all()
    
    if not books:
        print("❌ Книги не найдены в базе данных")
        return 1
    
    print(f"📚 Найдено книг: {len(books)}")
    print()
    
    # Показываем все названия книг из базы
    print("📋 Названия книг в базе данных:")
    for i, book in enumerate(books, 1):
        title = book.get("title", "Без названия")
        work_id = book.get("fantlab_work_id")
        series_id = book.get("fantlab_series_id")
        print(f"   {i}. '{title}' (work_id: {work_id}, series_id: {series_id})")
    print()
    
    # Показываем маппинг
    print("📋 Маппинг названий на work_id:")
    for key, work_id in BOOK_WORK_IDS.items():
        print(f"   '{key}' → {work_id}")
    print()
    
    updated_count = 0
    skipped_count = 0
    
    for book in books:
        book_id = book.get("id")
        book_title = book.get("title", "Без названия")
        current_work_id = book.get("fantlab_work_id")
        current_series_id = book.get("fantlab_series_id")
        
        # Определяем work_id для книги (с гибким поиском)
        work_id, matched_key = find_work_id(book_title)
        
        # Если ID не найден в маппинге, пропускаем
        if work_id is None:
            print(f"⏭️  Пропущена: '{book_title}' (ID не указан в маппинге)")
            print(f"   💡 Добавьте эту книгу в словарь BOOK_WORK_IDS")
            skipped_count += 1
            continue
        
        if matched_key != book_title:
            print(f"📖 '{book_title}' → найдено совпадение с '{matched_key}'")
        
        # Подготавливаем данные для обновления
        update_data = {}
        changes = []
        
        # Устанавливаем work_id (всегда обновляем, если значение отличается или force_update=True)
        if force_update or not current_work_id or current_work_id != work_id:
            update_data["fantlab_work_id"] = work_id
            if not current_work_id:
                changes.append(f"work_id: None → {work_id}")
                print(f"📖 '{book_title}': устанавливаем work_id = {work_id}")
            elif current_work_id != work_id:
                changes.append(f"work_id: {current_work_id} → {work_id}")
                print(f"📖 '{book_title}': обновляем work_id {current_work_id} → {work_id}")
            else:
                changes.append(f"work_id: {current_work_id} (принудительное обновление)")
                print(f"📖 '{book_title}': принудительно обновляем work_id = {work_id}")
        else:
            print(f"✓ '{book_title}': work_id уже установлен ({current_work_id})")
        
        # Устанавливаем series_id (всегда обновляем, если значение отличается или force_update=True)
        if force_update or not current_series_id or current_series_id != FANTLAB_SERIES_ID:
            update_data["fantlab_series_id"] = FANTLAB_SERIES_ID
            if not current_series_id:
                changes.append(f"series_id: None → {FANTLAB_SERIES_ID}")
                print(f"   Устанавливаем series_id = {FANTLAB_SERIES_ID}")
            elif current_series_id != FANTLAB_SERIES_ID:
                changes.append(f"series_id: {current_series_id} → {FANTLAB_SERIES_ID}")
                print(f"   Обновляем series_id {current_series_id} → {FANTLAB_SERIES_ID}")
            else:
                changes.append(f"series_id: {current_series_id} (принудительное обновление)")
                print(f"   Принудительно обновляем series_id = {FANTLAB_SERIES_ID}")
        
        # Обновляем в базе данных
        if update_data:
            try:
                print(f"   🔄 Обновление в базе данных: {', '.join(changes)}")
                result = BookRepositorySupabase.update(book_id, update_data)
                print(f"   ✅ Успешно обновлено в базе данных")
                updated_count += 1
            except Exception as e:
                print(f"   ❌ Ошибка при обновлении: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   ✓ Данные уже актуальны (work_id={current_work_id}, series_id={current_series_id})")
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
    parser = argparse.ArgumentParser(description="Установка FantLab ID для книг")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Принудительно обновить все значения, даже если они уже установлены"
    )
    
    args = parser.parse_args()
    
    try:
        sys.exit(main(force_update=args.force))
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

