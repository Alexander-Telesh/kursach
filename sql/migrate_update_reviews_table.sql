-- Миграция: Обновление таблицы reviews
-- Удаление поля rating, добавление полей для лайков и типов комментариев
-- Выполните этот скрипт в Supabase Dashboard → SQL Editor

-- Удаляем поле rating (если существует)
ALTER TABLE reviews 
DROP COLUMN IF EXISTS rating;

-- Добавляем поле likes_count для хранения количества лайков
ALTER TABLE reviews 
ADD COLUMN IF NOT EXISTS likes_count INTEGER DEFAULT 0;

-- Добавляем поле comment_type для различения комментариев и рецензий
ALTER TABLE reviews 
ADD COLUMN IF NOT EXISTS comment_type VARCHAR(50) DEFAULT 'comment';

-- Добавляем поле parent_comment_id для вложенных комментариев (опционально)
ALTER TABLE reviews 
ADD COLUMN IF NOT EXISTS parent_comment_id INTEGER REFERENCES reviews(id) ON DELETE CASCADE;

-- Создаем индекс для быстрого поиска по типу комментария
CREATE INDEX IF NOT EXISTS idx_reviews_comment_type 
ON reviews(comment_type);

-- Создаем индекс для поиска по количеству лайков
CREATE INDEX IF NOT EXISTS idx_reviews_likes_count 
ON reviews(likes_count DESC);

-- Комментарии к полям
COMMENT ON COLUMN reviews.likes_count IS 'Количество лайков у комментария/рецензии';
COMMENT ON COLUMN reviews.comment_type IS 'Тип записи: comment (комментарий) или review (рецензия)';
COMMENT ON COLUMN reviews.parent_comment_id IS 'ID родительского комментария (для вложенных комментариев)';

