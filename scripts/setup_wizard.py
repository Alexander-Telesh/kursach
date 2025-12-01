"""Интерактивный мастер настройки проекта."""
import sys
import os
from pathlib import Path

def print_header(text):
    """Печать заголовка."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def print_step(step_num, text):
    """Печать шага."""
    print(f"\n{'='*60}")
    print(f"ШАГ {step_num}: {text}")
    print(f"{'='*60}\n")

def check_python_version():
    """Проверка версии Python."""
    print_step(1, "Проверка версии Python")
    version = sys.version_info
    print(f"Текущая версия Python: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Требуется Python 3.9 или выше")
        return False
    else:
        print("✅ Версия Python подходит")
        return True

def install_dependencies():
    """Установка зависимостей."""
    print_step(2, "Установка зависимостей")
    
    response = input("Установить зависимости из requirements.txt? (y/n): ").lower()
    if response == 'y':
        print("\nВыполняется: pip install -r requirements.txt")
        os.system("pip install -r requirements.txt")
        print("\n✅ Зависимости установлены")
    else:
        print("⏭️  Пропущено. Установите вручную: pip install -r requirements.txt")

def create_env_file():
    """Создание файла .env."""
    print_step(3, "Создание файла .env")
    
    env_path = Path(".env")
    if env_path.exists():
        response = input("Файл .env уже существует. Перезаписать? (y/n): ").lower()
        if response != 'y':
            print("⏭️  Пропущено")
            return
    
    print("\nЗаполните данные для подключения к Supabase:")
    print("(Если у вас еще нет проекта Supabase, создайте его на https://supabase.com)\n")
    
    supabase_url = input("SUPABASE_URL (например: https://xxxxx.supabase.co): ").strip()
    supabase_key = input("SUPABASE_KEY (anon key из Settings → API): ").strip()
    supabase_db_url = input("SUPABASE_DB_URL (connection string из Settings → Database): ").strip()
    
    print("\nДанные для Litres API (опционально, можно оставить пустым):")
    litres_api_key = input("LITRES_API_KEY (или Enter для пропуска): ").strip()
    litres_api_url = input("LITRES_API_URL (по умолчанию: https://api.litres.ru): ").strip() or "https://api.litres.ru"
    
    # Создаем содержимое .env файла
    env_content = f"""# Supabase Configuration
SUPABASE_URL={supabase_url}
SUPABASE_KEY={supabase_key}
SUPABASE_DB_URL={supabase_db_url}

# Litres API Configuration
LITRES_API_KEY={litres_api_key}
LITRES_API_URL={litres_api_url}
"""
    
    try:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        print("\n✅ Файл .env создан успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка при создании .env: {e}")
        return False
    
    return True

def test_supabase():
    """Тестирование подключения к Supabase."""
    print_step(4, "Тестирование подключения к Supabase")
    
    response = input("Протестировать подключение к Supabase? (y/n): ").lower()
    if response != 'y':
        print("⏭️  Пропущено")
        return
    
    try:
        from database.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        test_connection = lambda: supabase.table("books").select("id").limit(1).execute()
        result = test_connection()
        if result != 0:
            print("\n❌ Тест не пройден. Проверьте настройки в .env файле")
            return False
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        return False
    
    return True

def init_database():
    """Инициализация базы данных."""
    print_step(5, "Инициализация базы данных")
    
    response = input("Создать таблицы в базе данных? (y/n): ").lower()
    if response != 'y':
        print("⏭️  Пропущено")
        return
    
    try:
        from scripts.init_database import main as init_main
        result = init_main()
        if result != 0:
            print("\n❌ Ошибка при инициализации")
            return False
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return False
    
    return True

def add_books():
    """Добавление книг."""
    print_step(6, "Добавление книг в базу данных")
    
    # Проверяем наличие FB2 файлов
    books_dir = Path("books")
    if not books_dir.exists():
        print("❌ Папка books/ не найдена")
        return False
    
    fb2_files = list(books_dir.glob("*.fb2"))
    if not fb2_files:
        print("❌ FB2 файлы не найдены в папке books/")
        return False
    
    print(f"Найдено FB2 файлов: {len(fb2_files)}")
    response = input("Добавить книги в базу данных? (y/n): ").lower()
    if response != 'y':
        print("⏭️  Пропущено")
        return
    
    try:
        from scripts.add_books_from_files import main as add_books_main
        result = add_books_main()
        if result != 0:
            print("\n❌ Ошибка при добавлении книг")
            return False
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return False
    
    return True

def main():
    """Основная функция мастера настройки."""
    print_header("МАСТЕР НАСТРОЙКИ ПРОЕКТА 'БАЗА ЗНАНИЙ СТЕЛЛАР'")
    
    print("Этот мастер поможет вам настроить проект пошагово.")
    print("Вы можете пропустить любой шаг, нажав 'n'.\n")
    
    input("Нажмите Enter для начала...")
    
    # Шаг 1: Проверка Python
    if not check_python_version():
        print("\n❌ Установите Python 3.9 или выше и запустите скрипт снова")
        return 1
    
    # Шаг 2: Установка зависимостей
    install_dependencies()
    
    # Шаг 3: Создание .env
    if not create_env_file():
        print("\n⚠️  Файл .env не создан. Создайте его вручную перед продолжением")
        response = input("Продолжить? (y/n): ").lower()
        if response != 'y':
            return 1
    
    # Шаг 4: Тест Supabase
    test_supabase()
    
    # Шаг 5: Инициализация БД
    init_database()
    
    # Шаг 6: Добавление книг
    add_books()
    
    # Финальное сообщение
    print_header("НАСТРОЙКА ЗАВЕРШЕНА!")
    
    print("✅ Проект настроен и готов к использованию!")
    print("\nСледующие шаги:")
    print("1. Запустите приложение: streamlit run app.py")
    print("2. Откройте браузер по адресу: http://localhost:8501")
    print("3. Проверьте работу всех страниц")
    print("\nДля развертывания на Streamlit Cloud см. DEPLOYMENT.md")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Настройка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)





