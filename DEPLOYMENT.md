# Инструкция по развертыванию

## Развертывание на Streamlit Cloud

### Шаг 1: Подготовка репозитория GitHub

1. Создайте репозиторий на GitHub
2. Загрузите код в репозиторий:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/your-repo.git
git push -u origin main
```

### Шаг 2: Настройка Streamlit Cloud

1. Зайдите на [Streamlit Cloud](https://share.streamlit.io/)
2. Войдите через GitHub
3. Нажмите "New app"
4. Выберите ваш репозиторий
5. Укажите:
   - **Main file path**: `app.py`
   - **Branch**: `main` (или ваша основная ветка)

### Шаг 3: Настройка переменных окружения

В настройках приложения на Streamlit Cloud добавьте следующие секреты (Secrets):

```toml
SUPABASE_URL = "your_supabase_project_url"
SUPABASE_KEY = "your_supabase_anon_key"
SUPABASE_DB_URL = "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"
LITRES_API_KEY = "your_litres_api_key"
LITRES_API_URL = "https://api.litres.ru"
```

Или используйте интерфейс Streamlit Cloud для добавления переменных окружения.

### Шаг 4: Настройка базы данных Supabase

1. Зарегистрируйтесь на [Supabase](https://supabase.com)
2. Создайте новый проект
3. Получите данные подключения:
   - **Project URL**: найдите в Settings > API
   - **Anon key**: найдите в Settings > API
   - **Database URL**: найдите в Settings > Database > Connection string
4. При первом запуске приложения таблицы создадутся автоматически

### Шаг 5: Создание индексов для полнотекстового поиска (опционально)

Для улучшения производительности полнотекстового поиска выполните в SQL Editor Supabase:

```sql
-- Создание индекса для полнотекстового поиска
CREATE INDEX IF NOT EXISTS books_search_idx 
ON books 
USING gin(to_tsvector('russian', 
    COALESCE(title, '') || ' ' || 
    COALESCE(author, '') || ' ' || 
    COALESCE(description, '')
));
```

### Шаг 6: Загрузка FB2 файлов

FB2 файлы можно загрузить:
1. Через GitHub (добавить в папку `books/`)
2. Через Supabase Storage (и указать путь в базе данных)
3. Через любой другой способ хранения файлов

### Шаг 7: Запуск приложения

После настройки всех переменных окружения приложение автоматически запустится на Streamlit Cloud.

## Локальное развертывание

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_DB_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
LITRES_API_KEY=your_litres_api_key
LITRES_API_URL=https://api.litres.ru
```

### Запуск

```bash
streamlit run app.py
```

## Добавление книг в базу данных

Книги можно добавить несколькими способами:

### Способ 1: Через SQL в Supabase

```sql
INSERT INTO books (title, author, description, series_order, fb2_file_path, litres_book_id)
VALUES 
('Название книги', 'Автор', 'Описание книги', 1, 'books/book1.fb2', 'litres_id_here');
```

### Способ 2: Через Python скрипт

Создайте файл `scripts/add_book.py`:

```python
from database.connection import get_db, init_db
from database.repository import BookRepository
from models.book import Book

init_db()
db = next(get_db())

book = Book(
    title="Название книги",
    author="Автор",
    description="Описание",
    series_order=1,
    fb2_file_path="books/book1.fb2",
    litres_book_id="litres_id"
)

BookRepository.create(db, book)
print("Книга добавлена!")
```

## Устранение неполадок

### Ошибка подключения к базе данных

- Проверьте правильность `SUPABASE_DB_URL`
- Убедитесь, что пароль в URL правильно экранирован
- Проверьте, что IP адрес не заблокирован в настройках Supabase

### Ошибка при создании таблиц

- Убедитесь, что у пользователя есть права на создание таблиц
- Проверьте логи в Supabase Dashboard

### FB2 файлы не находятся

- Проверьте путь к файлам в базе данных
- Убедитесь, что файлы находятся в папке `books/`
- Проверьте права доступа к файлам

### Ошибки Litres API

- Проверьте правильность API ключа
- Адаптируйте код под реальную структуру API Litres
- Проверьте rate limits API





