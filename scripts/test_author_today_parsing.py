"""Скрипт для тестирования парсинга комментариев и рецензий с AuthorToday."""
import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.author_today_api import AuthorToday
from utils.config import Config

def test_parsing(work_id: int):
    """Тестирует парсинг комментариев и рецензий для конкретного work_id."""
    print("=" * 70)
    print(f"Тестирование парсинга для work_id: {work_id}")
    print("=" * 70)
    print()
    
    # Проверка конфигурации
    login = Config.AUTHORTODAY_LOGIN
    password = Config.AUTHORTODAY_PASSWORD
    
    if not login or not password:
        print("❌ AUTHORTODAY_LOGIN и AUTHORTODAY_PASSWORD не установлены")
        return 1
    
    # Создание API
    api = AuthorToday()
    print("🔐 Авторизация...")
    login_result = api.login(login, password)
    
    if "error" in login_result or "token" not in login_result:
        print(f"❌ Ошибка авторизации: {login_result}")
        return 1
    
    print("✅ Авторизация успешна")
    print()
    
    # Тест получения комментариев
    print("📝 Тест получения комментариев...")
    comments = api.get_work_comments(work_id)
    print(f"   Найдено комментариев: {len(comments)}")
    
    if comments:
        print("   Примеры комментариев:")
        for i, comment in enumerate(comments[:3], 1):
            print(f"      {i}. Автор: {comment.get('author_name', 'N/A')}")
            print(f"         Текст: {comment.get('text', 'N/A')[:100]}...")
            print(f"         Лайки: {comment.get('likes_count', 0)}")
            print()
    else:
        print("   ⚠️  Комментарии не найдены")
    print()
    
    # Тест получения рецензий
    print("📄 Тест получения рецензий...")
    reviews = api.get_work_reviews(work_id)
    print(f"   Найдено рецензий: {len(reviews)}")
    
    if reviews:
        print("   Примеры рецензий:")
        for i, review in enumerate(reviews[:3], 1):
            print(f"      {i}. Автор: {review.get('author_name', 'N/A')}")
            print(f"         Текст: {review.get('text', 'N/A')[:100]}...")
            print(f"         Лайки: {review.get('likes_count', 0)}")
            print()
    else:
        print("   ⚠️  Рецензии не найдены")
    print()
    
    # Тест получения информации о работе
    print("📊 Тест получения информации о работе...")
    work_info = api.get_work_info(work_id)
    
    if "error" not in work_info:
        print(f"   Аннотация: {work_info.get('annotation', 'N/A')[:100]}...")
        print(f"   Статистика: {work_info.get('statistics', {})}")
    else:
        print(f"   ⚠️  Ошибка: {work_info.get('error')}")
    print()
    
    # Тест получения лайков
    print("❤️  Тест получения лайков...")
    likes = api.get_work_likes(work_id)
    print(f"   Лайков у работы: {likes}")
    print()
    
    print("=" * 70)
    print("✅ Тестирование завершено")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    # Можно передать work_id как аргумент
    if len(sys.argv) > 1:
        work_id = int(sys.argv[1])
    else:
        # Используем первый work_id из списка
        work_id = 79155  # Архив Стеллара
    
    try:
        sys.exit(test_parsing(work_id))
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

