"""Скрипт для проверки установленных зависимостей."""
import sys

def check_dependency(module_name, package_name=None):
    """Проверка наличия модуля."""
    if package_name is None:
        package_name = module_name
    
    try:
        __import__(module_name)
        print(f"✅ {package_name} установлен")
        return True
    except ImportError:
        print(f"❌ {package_name} НЕ установлен. Установите: pip install {package_name}")
        return False

def main():
    """Основная функция проверки."""
    print("=" * 50)
    print("Проверка зависимостей проекта")
    print("=" * 50)
    print()
    
    dependencies = [
        ("streamlit", "streamlit"),
        ("sqlalchemy", "sqlalchemy"),
        ("psycopg2", "psycopg2-binary"),
        ("supabase", "supabase"),
        ("requests", "requests"),
        ("bs4", "beautifulsoup4"),
        ("lxml", "lxml"),
        ("dotenv", "python-dotenv"),
    ]
    
    all_ok = True
    for module, package in dependencies:
        if not check_dependency(module, package):
            all_ok = False
    
    print()
    print("=" * 50)
    if all_ok:
        print("✅ Все зависимости установлены!")
        return 0
    else:
        print("❌ Некоторые зависимости отсутствуют")
        print("Установите недостающие: pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())





