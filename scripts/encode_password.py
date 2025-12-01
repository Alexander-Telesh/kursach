"""Утилита для кодирования пароля в URL."""
import urllib.parse
import sys

def encode_password_for_url(password):
    """
    Кодирует пароль для использования в PostgreSQL connection string.
    
    Кодирует только символы, которые обязательно нужно кодировать.
    Символы _, !, -, . и другие безопасные остаются без изменений.
    """
    # Символы, которые обязательно нужно кодировать
    must_encode = ['@', '#', '$', '%', '&', '+', '=', '?', '/', ' ']
    
    encoded = ""
    for char in password:
        if char in must_encode:
            encoded += urllib.parse.quote(char, safe='')
        else:
            encoded += char
    
    return encoded

def main():
    """Интерактивная утилита для кодирования пароля."""
    print("=" * 70)
    print("Утилита кодирования пароля для PostgreSQL Connection String")
    print("=" * 70)
    print()
    print("Эта утилита поможет закодировать специальные символы в пароле.")
    print("Символы _, !, -, . и другие безопасные остаются без изменений.")
    print()
    
    if len(sys.argv) > 1:
        # Пароль передан как аргумент
        password = sys.argv[1]
    else:
        # Интерактивный ввод
        password = input("Введите пароль: ").strip()
    
    if not password:
        print("❌ Пароль не может быть пустым!")
        return 1
    
    encoded = encode_password_for_url(password)
    
    print()
    print("=" * 70)
    print("РЕЗУЛЬТАТ:")
    print("=" * 70)
    print()
    print(f"Оригинальный пароль: {password}")
    print(f"Закодированный:      {encoded}")
    print()
    
    # Показываем, какие символы были закодированы
    changed = []
    for i, (orig, enc) in enumerate(zip(password, encoded)):
        if orig != enc:
            changed.append(f"{orig} → {enc[i] if i < len(encoded) else '?'}")
    
    if changed:
        print("Закодированные символы:")
        for change in changed:
            print(f"  {change}")
    else:
        print("✅ Все символы безопасны, кодирование не требуется!")
        print("   (Символы _, !, -, . и другие безопасные остались без изменений)")
    
    print()
    print("=" * 70)
    print("ИСПОЛЬЗОВАНИЕ:")
    print("=" * 70)
    print()
    print("В Connection String замените [YOUR-PASSWORD] на:")
    print(f"  {encoded}")
    print()
    print("Пример полного Connection String:")
    print(f"  postgresql://postgres:{encoded}@db.xxxxx.supabase.co:5432/postgres")
    print()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")
        sys.exit(1)




