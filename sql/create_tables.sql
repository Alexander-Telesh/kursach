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
    fantlab_work_id INTEGER,
    fantlab_series_id INTEGER,
    fantlab_rating FLOAT,
    fantlab_voters_count INTEGER DEFAULT 0,
    fantlab_reviews_count INTEGER DEFAULT 0,
    fantlab_annotation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Индексы для books
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_fantlab_work_id ON books(fantlab_work_id);
CREATE INDEX IF NOT EXISTS idx_books_fantlab_series_id ON books(fantlab_series_id);

-- Создание таблицы reviews
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    fantlab_review_id VARCHAR(100) UNIQUE,
    author_name VARCHAR(255),
    text TEXT,
    date TIMESTAMP WITH TIME ZONE,
    likes_count INTEGER DEFAULT 0,
    comment_type VARCHAR(50) DEFAULT 'comment' CHECK (comment_type IN ('comment', 'review')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Индексы для reviews
CREATE INDEX IF NOT EXISTS idx_reviews_book_id ON reviews(book_id);
CREATE INDEX IF NOT EXISTS idx_reviews_fantlab_id ON reviews(fantlab_review_id);
CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(date DESC);


