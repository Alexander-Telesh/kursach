-- Миграция: Добавление поля author_today_work_id в таблицу books
-- Выполните этот скрипт в Supabase Dashboard → SQL Editor

-- Добавляем поле author_today_work_id
ALTER TABLE books 
ADD COLUMN IF NOT EXISTS author_today_work_id INTEGER;

-- Создаем индекс для быстрого поиска по work_id
CREATE INDEX IF NOT EXISTS idx_books_author_today_work_id 
ON books(author_today_work_id);

-- Комментарий к полю
COMMENT ON COLUMN books.author_today_work_id IS 'ID произведения на AuthorToday (извлекается из URL: author.today/work/{id})';

