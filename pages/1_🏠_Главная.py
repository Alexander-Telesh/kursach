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

col1, col2, col3 = st.columns(3)

books_data = BookRepositorySupabase.get_all()
books = dicts_to_books(books_data)
total_books = len(books)

with col1:
    st.metric("Количество книг", total_books)

# Средний рейтинг серии
avg_rating = ReviewRepositorySupabase.get_series_average_rating()
with col2:
    if avg_rating:
        st.metric("Средний рейтинг серии", f"{avg_rating:.2f} ⭐")
    else:
        st.metric("Средний рейтинг серии", "Нет данных")

# Общее количество отзывов
all_reviews_data = ReviewRepositorySupabase.get_all_recent(limit=1000)
total_reviews = len(all_reviews_data)
with col3:
    st.metric("Всего отзывов", total_reviews)

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
                
                # Рейтинг
                if review.rating:
                    stars = "⭐" * int(review.rating)
                    st.write(f"**Оценка:** {review.rating:.1f} {stars}")
                
                # Текст отзыва
                if review.text:
                    st.write(review.text)
                else:
                    st.write("*Отзыв без текста*")
            
            with col2:
                if review.rating:
                    st.metric("Оценка", f"{review.rating:.1f}")
            
            st.markdown("---")
else:
    st.info("Пока нет отзывов. Обновите отзывы с AuthorToday, чтобы увидеть их здесь.")
