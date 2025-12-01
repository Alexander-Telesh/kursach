"""Главная страница с общей информацией о серии и отзывами."""
import streamlit as st
from database.repository_supabase import BookRepositorySupabase, ReviewRepositorySupabase
from database.helpers import dicts_to_books, dicts_to_reviews
from services.author_today_api import sync_reviews_from_author_today
from datetime import datetime

st.title("🏠 Главная страница")
st.markdown("---")

# Общая информация о серии
st.header("📖 О серии 'Стеллар'")
st.markdown("""
Серия книг "Стеллар" - это увлекательная фантастическая сага, которая захватывает читателей 
своим уникальным миром и персонажами. Здесь вы найдете всю информацию о книгах серии, 
отзывы читателей и возможность прочитать произведения онлайн.
""")

# Статистика
st.header("📊 Статистика")

col1, col2, col3, col4 = st.columns(4)

books_data = BookRepositorySupabase.get_all()
books = dicts_to_books(books_data)
total_books = len(books)

with col1:
    st.metric("Количество книг", total_books)

# Подсчитываем статистику по всем книгам
total_comments = 0
total_reviews = 0
total_likes = 0

for book in books_data:
    book_id = book.get("id")
    comments_data = ReviewRepositorySupabase.get_by_book_id_and_type(book_id, "comment")
    reviews_data = ReviewRepositorySupabase.get_by_book_id_and_type(book_id, "review")
    total_comments += len(comments_data) if comments_data else 0
    total_reviews += len(reviews_data) if reviews_data else 0
    total_likes += ReviewRepositorySupabase.get_total_likes_for_book(book_id)

with col2:
    st.metric("Комментариев", total_comments)

with col3:
    st.metric("Рецензий", total_reviews)

with col4:
    st.metric("Всего лайков", total_likes)

st.markdown("---")

# Обновление отзывов
st.header("🔄 Обновление отзывов с AuthorToday")

col1, col2 = st.columns([3, 1])

with col1:
    st.info("Нажмите кнопку для обновления отзывов с ресурса AuthorToday. Это может занять некоторое время.")

with col2:
    if st.button("🔄 Обновить отзывы", type="primary"):
        with st.spinner("Обновление отзывов..."):
            result = sync_reviews_from_author_today()
            if result.get("success"):
                st.success(f"✅ Обновлено {result.get('total_reviews', 0)} отзывов для {result.get('updated_books', 0)} книг")
                st.rerun()
            else:
                st.error(f"❌ {result.get('error', 'Неизвестная ошибка')}")

st.markdown("---")

# Последние отзывы
st.header("💬 Последние отзывы")

recent_reviews_data = ReviewRepositorySupabase.get_all_recent(limit=10)
recent_reviews = dicts_to_reviews(recent_reviews_data)

if recent_reviews:
    for review in recent_reviews:
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Название книги
                book_data = BookRepositorySupabase.get_by_id(review.book_id)
                book_title = book_data.get("title") if book_data else "Неизвестная книга"
                st.subheader(f"📖 {book_title}")
                
                # Автор отзыва и дата
                author_info = review.author_name or "Анонимный читатель"
                date_info = ""
                if review.date:
                    if isinstance(review.date, str):
                        try:
                            date_obj = datetime.fromisoformat(review.date.replace("Z", "+00:00"))
                            date_info = f" • {date_obj.strftime('%d.%m.%Y')}"
                        except:
                            pass
                    else:
                        date_info = f" • {review.date.strftime('%d.%m.%Y')}"
                st.caption(f"👤 {author_info}{date_info}")
                
                # Лайки
                if review.likes_count and review.likes_count > 0:
                    st.write(f"❤️ **{review.likes_count}** лайков")
                
                # Тип (комментарий или рецензия)
                if review.comment_type == "review":
                    st.caption("📄 Рецензия")
                else:
                    st.caption("💬 Комментарий")
                
                # Текст отзыва
                if review.text:
                    st.write(review.text)
                else:
                    st.write("*Отзыв без текста*")
            
            with col2:
                if review.likes_count and review.likes_count > 0:
                    st.metric("❤️", review.likes_count)
            
            st.markdown("---")
else:
    st.info("Пока нет отзывов. Обновите отзывы с AuthorToday, чтобы увидеть их здесь.")
