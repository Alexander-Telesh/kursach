-- SQL скрипт для создания таблиц в Supabase
-- Выполните этот скрипт в Supabase Dashboard → SQL Editor

-- Создание таблицы books
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    description TEXT,
    series_order INTEGER,
    fb2_file_path VARCHAR(500),
    litres_book_id VARCHAR(100) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Индексы для books
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_litres_id ON books(litres_book_id);

-- Создание таблицы reviews
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    litres_review_id VARCHAR(100) UNIQUE,
    author_name VARCHAR(255),
    rating FLOAT,
    text TEXT,
    date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Индексы для reviews
CREATE INDEX IF NOT EXISTS idx_reviews_book_id ON reviews(book_id);
CREATE INDEX IF NOT EXISTS idx_reviews_litres_id ON reviews(litres_review_id);
CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(date DESC);

-- Проверка создания таблиц
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('books', 'reviews');

