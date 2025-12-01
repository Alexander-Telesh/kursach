"""Интерактивный скрипт для создания файла .env."""
import os
import sys
from pathlib import Path

def print_header(text):
    """Печать заголовка."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def create_env_file():
    """Интерактивное создание файла .env."""
    print_header("СОЗДАНИЕ ФАЙЛА .env")
    
    env_path = Path(".env")
    
    # Проверка существующего файла
    if env_path.exists():
        print("⚠️  Файл .env уже существует!")
        response = input("Перезаписать существующий файл? (y/n): ").lower().strip()
        if response != 'y':
            print("❌ Отменено. Существующий файл сохранен.")
            return False
        print()
    
    print("Заполните данные для подключения к Supabase.")
    print("Если у вас еще нет проекта Supabase, создайте его на https://supabase.com")
    print()
    print("=" * 70)
    print("ШАГ 1: Данные Supabase")
    print("=" * 70)
    print()
    
    # Supabase URL
    print("1. SUPABASE_URL")
    print("   Это Project URL из Settings → API")
    print("   Пример: https://abcdefghijklmnop.supabase.co")
    supabase_url = input("   Введите SUPABASE_URL: ").strip()
    
    if not supabase_url:
        print("❌ SUPABASE_URL не может быть пустым!")
        return False
    
    if not supabase_url.startswith("https://"):
        print("⚠️  URL должен начинаться с https://")
        response = input("   Продолжить? (y/n): ").lower().strip()
        if response != 'y':
            return False
    
    print()
    
    # Supabase Key
    print("2. SUPABASE_KEY")
    print("   Это anon public key из Settings → API → Project API keys")
    print("   Длинная строка, начинается с eyJ...")
    supabase_key = input("   Введите SUPABASE_KEY: ").strip()
    
    if not supabase_key:
        print("❌ SUPABASE_KEY не может быть пустым!")
        return False
    
    print()
    
    # Database URL
    print("3. SUPABASE_DB_URL")
    print("   Это Connection string из Settings → Database → URI")
    print("   ВАЖНО: Замените [YOUR-PASSWORD] на ваш реальный пароль!")
    print("   Пример: postgresql://postgres:MyPass@123@db.xxxxx.supabase.co:5432/postgres")
    print()
    print("   Если в пароле есть специальные символы, закодируйте их:")
    print("   @ → %40, # → %23, $ → %24, % → %25, & → %26, + → %2B")
    print()
    supabase_db_url = input("   Введите SUPABASE_DB_URL: ").strip()
    
    if not supabase_db_url:
        print("❌ SUPABASE_DB_URL не может быть пустым!")
        return False
    
    if "[YOUR-PASSWORD]" in supabase_db_url:
        print("❌ ОШИБКА: Вы не заменили [YOUR-PASSWORD] на реальный пароль!")
        return False
    
    print()
    print("=" * 70)
    print("ШАГ 2: Данные AuthorToday API (опционально)")
    print("=" * 70)
    print()
    print("Для работы с AuthorToday API нужны логин и пароль от аккаунта.")
    print("Если у вас их нет, просто нажмите Enter для всех полей.")
    print("Подробнее: см. AUTHORTODAY_API_SETUP.md")
    print()
    
    authortoday_api_url = input("AUTHORTODAY_API_URL (по умолчанию: https://api.author.today): ").strip()
    if not authortoday_api_url:
        authortoday_api_url = "https://api.author.today"
    
    authortoday_web_url = input("AUTHORTODAY_WEB_URL (по умолчанию: https://author.today): ").strip()
    if not authortoday_web_url:
        authortoday_web_url = "https://author.today"
    
    authortoday_login = input("AUTHORTODAY_LOGIN (логин от AuthorToday, или Enter для пропуска): ").strip()
    authortoday_password = input("AUTHORTODAY_PASSWORD (пароль от AuthorToday, или Enter для пропуска): ").strip()
    authortoday_token = input("AUTHORTODAY_TOKEN (оставьте пустым, получается автоматически): ").strip()
    
    # Создание содержимого файла
    env_content = f"""# Supabase Configuration
SUPABASE_URL={supabase_url}
SUPABASE_KEY={supabase_key}
SUPABASE_DB_URL={supabase_db_url}

# AuthorToday API Configuration
AUTHORTODAY_API_URL={authortoday_api_url}
AUTHORTODAY_WEB_URL={authortoday_web_url}
AUTHORTODAY_LOGIN={authortoday_login}
AUTHORTODAY_PASSWORD={authortoday_password}
AUTHORTODAY_TOKEN={authortoday_token}
"""
    
    # Показываем предпросмотр
    print()
    print("=" * 70)
    print("ПРЕДПРОСМОТР ФАЙЛА .env")
    print("=" * 70)
    print()
    print(env_content)
    print("=" * 70)
    print()
    
    # Подтверждение
    response = input("Создать файл .env с этими данными? (y/n): ").lower().strip()
    if response != 'y':
        print("❌ Отменено.")
        return False
    
    # Сохранение файла
    try:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        print()
        print("✅ Файл .env успешно создан!")
        print()
        print("⚠️  ВАЖНО:")
        print("   - Файл .env уже добавлен в .gitignore")
        print("   - НЕ коммитьте его в Git!")
        print("   - Храните его в безопасности")
        print()
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании файла: {e}")
        return False

def main():
    """Основная функция."""
    try:
        success = create_env_file()
        if success:
            print("=" * 70)
            print("СЛЕДУЮЩИЕ ШАГИ:")
            print("=" * 70)
            print()
            print("1. Проверьте подключение:")
            print("   python scripts/test_supabase_connection.py")
            print()
            print("2. Инициализируйте базу данных:")
            print("   python scripts/init_database.py")
            print()
            print("3. Добавьте книги:")
            print("   python scripts/add_books_from_files.py")
            print()
            print("4. Запустите приложение:")
            print("   streamlit run app.py")
            print()
            return 0
        else:
            return 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        return 1
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

