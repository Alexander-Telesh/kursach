"""Скрипт для проверки настройки MCP Supabase."""
import sys
import json
from pathlib import Path

def check_mcp_config():
    """Проверка конфигурации MCP."""
    print("=" * 70)
    print("Проверка настройки MCP Supabase")
    print("=" * 70)
    print()
    
    # Проверка файла конфигурации
    print("1. Проверка файла .cursor/mcp.json...")
    mcp_config_path = Path(".cursor/mcp.json")
    
    if not mcp_config_path.exists():
        print("   ❌ Файл .cursor/mcp.json не найден!")
        print()
        print("   Решение:")
        print("   1. Скопируйте .cursor/mcp.json.example в .cursor/mcp.json")
        print("   2. Заполните реальные значения SUPABASE_URL и SUPABASE_ACCESS_TOKEN")
        return 1
    
    print("   ✅ Файл .cursor/mcp.json найден")
    
    # Проверка содержимого
    try:
        with open(mcp_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("   ✅ Файл содержит валидный JSON")
        
        # Проверка структуры
        if "mcpServers" not in config:
            print("   ❌ Отсутствует ключ 'mcpServers'")
            return 1
        
        if "supabase" not in config["mcpServers"]:
            print("   ❌ Отсутствует конфигурация 'supabase'")
            return 1
        
        supabase_config = config["mcpServers"]["supabase"]
        
        # Проверка переменных окружения
        if "env" not in supabase_config:
            print("   ❌ Отсутствует секция 'env'")
            return 1
        
        env = supabase_config["env"]
        
        supabase_url = env.get("SUPABASE_URL", "")
        access_token = env.get("SUPABASE_ACCESS_TOKEN", "")
        
        if not supabase_url or supabase_url == "your_supabase_project_url":
            print("   ❌ SUPABASE_URL не заполнен или содержит placeholder")
            return 1
        
        if not access_token or access_token == "your_personal_access_token":
            print("   ❌ SUPABASE_ACCESS_TOKEN не заполнен или содержит placeholder")
            return 1
        
        print(f"   ✅ SUPABASE_URL: {supabase_url[:40]}...")
        print(f"   ✅ SUPABASE_ACCESS_TOKEN: {access_token[:20]}...")
        
    except json.JSONDecodeError as e:
        print(f"   ❌ Ошибка парсинга JSON: {e}")
        return 1
    except Exception as e:
        print(f"   ❌ Ошибка при чтении файла: {e}")
        return 1
    
    print()
    
    # Проверка Node.js
    print("2. Проверка Node.js...")
    import subprocess
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"   ✅ Node.js установлен: {result.stdout.strip()}")
        else:
            print("   ❌ Node.js не найден")
            print("   Установите Node.js: https://nodejs.org/")
            return 1
    except FileNotFoundError:
        print("   ❌ Node.js не установлен")
        print("   Установите Node.js: https://nodejs.org/")
        return 1
    except Exception as e:
        print(f"   ⚠️  Не удалось проверить Node.js: {e}")
    
    print()
    
    # Проверка npx
    print("3. Проверка npx...")
    try:
        result = subprocess.run(["npx", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"   ✅ npx доступен: {result.stdout.strip()}")
        else:
            print("   ⚠️  npx не найден (обычно идет с Node.js)")
    except FileNotFoundError:
        print("   ⚠️  npx не найден (обычно идет с Node.js)")
    except Exception as e:
        print(f"   ⚠️  Не удалось проверить npx: {e}")
    
    print()
    
    # Проверка .env файла
    print("4. Проверка .env файла...")
    env_path = Path(".env")
    if env_path.exists():
        print("   ✅ Файл .env существует")
        
        # Проверяем наличие необходимых переменных
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        supabase_url_env = os.getenv("SUPABASE_URL", "")
        supabase_key_env = os.getenv("SUPABASE_KEY", "")
        
        if supabase_url_env:
            print(f"   ✅ SUPABASE_URL в .env: {supabase_url_env[:40]}...")
        else:
            print("   ⚠️  SUPABASE_URL не найден в .env")
        
        if supabase_key_env:
            print("   ✅ SUPABASE_KEY в .env: установлен")
        else:
            print("   ⚠️  SUPABASE_KEY не найден в .env")
        
        # Проверяем соответствие URL
        if supabase_url_env and supabase_url_env == supabase_url:
            print("   ✅ SUPABASE_URL совпадает в .env и mcp.json")
        elif supabase_url_env:
            print("   ⚠️  SUPABASE_URL отличается в .env и mcp.json")
    else:
        print("   ⚠️  Файл .env не найден")
    
    print()
    print("=" * 70)
    print("✅ Проверка завершена!")
    print("=" * 70)
    print()
    print("Следующие шаги:")
    print("1. Если все проверки прошли успешно, перезапустите Cursor")
    print("2. После перезапуска MCP Supabase будет доступен")
    print("3. Вы сможете задавать вопросы о базе данных через ИИ-ассистента")
    print()
    print("Примеры использования в Cursor:")
    print("- 'Покажи все книги в базе данных'")
    print("- 'Сколько отзывов у книги с ID 1?'")
    print("- 'Выполни SELECT * FROM books LIMIT 5'")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(check_mcp_config())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



