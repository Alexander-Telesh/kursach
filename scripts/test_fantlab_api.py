"""Тестовый скрипт для проверки работы FantLab API."""
import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fantlab_api import FantLab

def test_fantlab_api():
    """Тестирует работу FantLab API."""
    print("=" * 70)
    print("Тестирование FantLab API")
    print("=" * 70)
    print()
    
    api = FantLab()
    
    # Тестовые ID
    test_work_id = 1597211  # Первая книга серии
    test_series_id = 1597163  # Цикл "Стеллар"
    
    print(f"API URL: {api.api_url}")
    print(f"Web URL: {api.web_url}")

    print()
    
    # Тест 1: Информация о произведении
    print("Тест 1: Получение информации о произведении")
    print("-" * 70)
    print(f"Запрос к /work/{test_work_id}...")
    work_info = api.get_work_info(test_work_id)
    if "error" in work_info:
        print(f"❌ Ошибка: {work_info['error']}")
    else:
        print(f"✅ Название: {work_info.get('title', 'N/A')}")
        print(f"✅ Автор: {work_info.get('author', 'N/A')}")
        print(f"✅ Рейтинг: {work_info.get('rating', 0.0):.2f}")
        print(f"✅ Количество оценок: {work_info.get('voters_count', 0)}")
        print(f"✅ Количество отзывов: {work_info.get('reviews_count', 0)}")
        print(f"✅ Аннотация (первые 100 символов): {work_info.get('annotation', '')[:100]}...")
    print()
    
    # Тест 2: Расширенная информация о произведении
    print("Тест 2: Получение расширенной информации о произведении")
    print("-" * 70)
    print(f"Запрос к /work/{test_work_id}/extended...")
    extended_info = api.get_work_info_extended(test_work_id)
    if "error" in extended_info:
        print(f"❌ Ошибка: {extended_info['error']}")
    else:
        print(f"✅ Базовая информация получена")
        if extended_info.get("awards"):
            print(f"✅ Награды: найдено")
        if extended_info.get("translations"):
            print(f"✅ Переводы: найдено")
        if extended_info.get("children"):
            print(f"✅ Дочерние произведения: {len(extended_info.get('children', []))}")
    print()
    
    # Тест 3: Отзывы на произведение
    print("Тест 3: Получение отзывов на произведение")
    print("-" * 70)
    print(f"Запрос отзывов для work_id={test_work_id}...")
    reviews = api.get_work_reviews(test_work_id)
    print(f"✅ Найдено отзывов: {len(reviews)}")
    if reviews:
        first_review = reviews[0]
        print(f"✅ Первый отзыв:")
        print(f"   - ID: {first_review.get('id', 'N/A')}")
        print(f"   - Автор: {first_review.get('author_name', 'N/A')}")
        print(f"   - Оценка: {first_review.get('rating', 0.0)}")
        print(f"   - Лайков: {first_review.get('likes_count', 0)}")
        print(f"   - Текст (первые 100 символов): {first_review.get('text', '')[:100]}...")
    else:
        print("⚠️ Отзывы не найдены (возможно, их нет или требуется HTML fallback)")
    print()
    
    # Тест 4: Информация о цикле
    print("Тест 4: Получение информации о цикле")
    print("-" * 70)
    print(f"Запрос к /work/{test_series_id}...")
    series_info = api.get_series_info(test_series_id)
    if "error" in series_info:
        print(f"❌ Ошибка: {series_info['error']}")
    else:
        print(f"✅ Название: {series_info.get('title', 'N/A')}")
        print(f"✅ Рейтинг: {series_info.get('rating', 0.0):.2f}")
        print(f"✅ Количество оценок: {work_info.get('voters_count', 0)}")
        print(f"✅ Количество отзывов: {series_info.get('reviews_count', 0)}")
        print(f"✅ Произведений в цикле: {len(series_info.get('works', []))}")
        print(f"✅ Аннотация (первые 100 символов): {series_info.get('annotation', '')[:100]}...")
    print()
    
    # Тест 5: Отзывы на цикл
    print("Тест 5: Получение отзывов на цикл")
    print("-" * 70)
    print(f"Запрос отзывов для series_id={test_series_id}...")
    series_reviews = api.get_series_reviews(test_series_id)
    print(f"✅ Найдено отзывов: {len(series_reviews)}")
    if series_reviews:
        print(f"✅ Первый отзыв: {series_reviews[0].get('author_name', 'N/A')}")
    else:
        print("⚠️ Отзывы не найдены")
    print()
    
    print("=" * 70)
    print("Тестирование завершено")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_fantlab_api()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
