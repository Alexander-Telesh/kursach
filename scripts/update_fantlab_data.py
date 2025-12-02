"""Скрипт для принудительного обновления данных FantLab для всех книг."""
import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.repository_supabase import BookRepositorySupabase
from services.fantlab_api import FantLab
import time

def main():
    """Обновить данные FantLab для всех книг."""
    print("=" * 70)
    print("Обновление данных FantLab для всех книг")
    print("=" * 70)
    print()
    
    # Получаем все книги
    books = BookRepositorySupabase.get_all()
    
    if not books:
        print("❌ Книги не найдены в базе данных")
        return 1
    
    print(f"📚 Найдено книг: {len(books)}")
    print()
    
    api = FantLab()
    updated_count = 0
    error_count = 0
    
    for book in books:
        book_id = book.get("id")
        book_title = book.get("title", "Без названия")
        work_id = book.get("fantlab_work_id")
        
        if not work_id:
            print(f"⏭️  Пропущена: '{book_title}' (нет fantlab_work_id)")
            continue
        
        print(f"📖 Обработка: '{book_title}' (ID: {book_id}, work_id: {work_id})")
        
        try:
            # Получаем информацию о произведении
            work_info = api.get_work_info(work_id)
            
            if "error" in work_info:
                print(f"   ❌ Ошибка получения данных: {work_info.get('error')}")
                error_count += 1
                continue
            
            # Подготавливаем данные для обновления
            update_data = {}
            
            # Основные данные
            if work_info.get("title"):
                update_data["title"] = work_info.get("title")
            if work_info.get("author"):
                update_data["author"] = work_info.get("author")
            
            # Аннотация
            annotation = work_info.get("annotation", "")
            if annotation:
                update_data["description"] = annotation
                update_data["fantlab_annotation"] = annotation
            else:
                update_data["fantlab_annotation"] = None
            
            # Метрики FantLab
            update_data["fantlab_rating"] = work_info.get("rating") if work_info.get("rating") else None
            update_data["fantlab_voters_count"] = work_info.get("voters_count", 0)
            update_data["fantlab_reviews_count"] = work_info.get("reviews_count", 0)
            
            # Обновляем в базе данных
            result = BookRepositorySupabase.update(book_id, update_data)
            
            print(f"   ✅ Обновлено:")
            print(f"      - Рейтинг: {update_data.get('fantlab_rating', 'NULL')}")
            print(f"      - Оценок: {update_data.get('fantlab_voters_count', 0)}")
            print(f"      - Отзывов: {update_data.get('fantlab_reviews_count', 0)}")
            print(f"      - Аннотация: {'есть' if update_data.get('fantlab_annotation') else 'нет'}")
            
            updated_count += 1
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            error_count += 1
        
        # Небольшая задержка между запросами, чтобы не перегружать API
        time.sleep(0.5)
        print()
    
    print("=" * 70)
    print("Результаты:")
    print(f"  ✅ Обновлено: {updated_count}")
    print(f"  ❌ Ошибок: {error_count}")
    print(f"  ⏭️  Пропущено: {len(books) - updated_count - error_count}")
    print("=" * 70)
    
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

