"""Скрипт для тестирования парсера AuthorToday API."""
import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.author_today_api import AuthorToday, sync_reviews_from_author_today
from utils.config import Config

def test_author_today_api():
    """Тестирует работу AuthorToday API."""
    print("=" * 70)
    print("Тестирование AuthorToday API")
    print("=" * 70)
    print()
    
    # Проверка конфигурации
    print("1. Проверка конфигурации...")
    login = Config.AUTHORTODAY_LOGIN
    password = Config.AUTHORTODAY_PASSWORD
    
    if not login or not password:
        print("   ❌ AUTHORTODAY_LOGIN и AUTHORTODAY_PASSWORD не установлены")
        print("   Установите их в .env файле или Streamlit secrets")
        return 1
    
    print(f"   ✅ Логин: {login}")
    print(f"   ✅ Пароль: {'*' * len(password)}")
    print()
    
    # Создание экземпляра API
    print("2. Создание экземпляра API...")
    api = AuthorToday()
    print(f"   ✅ API URL: {api.api}")
    print(f"   ✅ Web API URL: {api.web_api}")
    print()
    
    # Тест авторизации
    print("3. Тест авторизации...")
    login_result = api.login(login, password)
    
    if "error" in login_result:
        print(f"   ❌ Ошибка авторизации: {login_result.get('error')}")
        return 1
    
    if "token" not in login_result:
        print(f"   ❌ Токен не получен. Ответ: {login_result}")
        return 1
    
    print("   ✅ Авторизация успешна")
    print(f"   ✅ Токен получен: {login_result.get('token', '')[:20]}...")
    print()
    
    # Тест поиска
    print("4. Тест поиска произведений...")
    test_query = "Инкарнатор"
    print(f"   Поиск по запросу: '{test_query}'")
    
    works = api.search_work(test_query)
    
    if not works:
        print("   ⚠️  Произведения не найдены")
    else:
        print(f"   ✅ Найдено произведений: {len(works)}")
        for i, work in enumerate(works[:3], 1):
            work_id = work.get("id") or work.get("workId") or work.get("work_id") or work.get("Id")
            work_title = work.get("title") or work.get("Title") or "Без названия"
            work_author = work.get("authorName") or work.get("author") or work.get("AuthorName") or "Неизвестный автор"
            print(f"      {i}. {work_title} - {work_author} (ID: {work_id})")
    print()
    
    # Тест получения отзывов (если найдено произведение)
    if works:
        print("5. Тест получения отзывов...")
        first_work = works[0]
        work_id = first_work.get("id") or first_work.get("workId") or first_work.get("work_id") or first_work.get("Id")
        
        if work_id:
            print(f"   Получение отзывов для work_id: {work_id}")
            reviews = api.get_work_reviews(work_id)
            
            if reviews:
                print(f"   ✅ Найдено отзывов: {len(reviews)}")
                for i, review in enumerate(reviews[:3], 1):
                    author = review.get("author") or review.get("userName") or review.get("authorName") or "Аноним"
                    rating = review.get("rating") or review.get("score") or review.get("stars") or "N/A"
                    text_preview = (review.get("text") or review.get("content") or review.get("comment") or "")[:50]
                    print(f"      {i}. {author} - {rating}⭐: {text_preview}...")
            else:
                print("   ⚠️  Отзывы не найдены через API")
        else:
            print("   ⚠️  ID произведения не найден")
    else:
        print("5. Пропуск теста отзывов (произведения не найдены)")
    print()
    
    # Тест полной синхронизации (только для одной книги)
    print("6. Тест синхронизации отзывов (только для одной книги)...")
    print("   Для полной синхронизации используйте функцию sync_reviews_from_author_today()")
    print("   в Streamlit приложении или передайте book_id")
    print()
    
    print("=" * 70)
    print("✅ Тестирование завершено!")
    print("=" * 70)
    print()
    print("Для синхронизации отзывов используйте:")
    print("  - В Streamlit: кнопка 'Обновить отзывы' на главной странице")
    print("  - В коде: sync_reviews_from_author_today(book_id=1)")
    print()
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(test_author_today_api())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

