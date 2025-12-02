"""Главная страница с общей информацией о серии и отзывами."""
import streamlit as st
from database.repository_supabase import BookRepositorySupabase, ReviewRepositorySupabase
from database.helpers import dicts_to_books, dicts_to_reviews
from services.fantlab_api import sync_reviews_from_fantlab, FantLab
from datetime import datetime

st.title("🏠 Главная страница")
st.markdown("---")

# Получаем данные о книгах
books_data = BookRepositorySupabase.get_all()
books = dicts_to_books(books_data)

# Общая информация о серии
st.header("📖 О серии 'Стеллар'")

# Получаем информацию о цикле с FantLab (если есть series_id)
if books_data:
    first_book = books_data[0]
    series_id = first_book.get("fantlab_series_id")
    
    if series_id:
        try:
            api = FantLab()
            series_info = api.get_series_info(series_id)
            
            if "error" not in series_info:
                # Аннотация цикла
                if series_info.get("annotation"):
                    st.markdown(series_info["annotation"])
                else:
                    st.markdown("""
                    Серия книг "Стеллар" - это увлекательная фантастическая сага, которая захватывает читателей 
                    своим уникальным миром и персонажами. Здесь вы найдете всю информацию о книгах серии, 
                    отзывы читателей и возможность прочитать произведения онлайн.
                    """)
                
                # Оценка цикла
                series_rating = series_info.get("rating", 0.0)
                if series_rating > 0:
                    col1, col2 = st.columns([3, 1])
                    with col2:
                        st.metric("⭐ Оценка цикла", f"{series_rating:.2f}")
            else:
                st.markdown("""
                Серия книг "Стеллар" - это увлекательная фантастическая сага, которая захватывает читателей 
                своим уникальным миром и персонажами. Здесь вы найдете всю информацию о книгах серии, 
                отзывы читателей и возможность прочитать произведения онлайн.
                """)
        except:
            st.markdown("""
            Серия книг "Стеллар" - это увлекательная фантастическая сага, которая захватывает читателей 
            своим уникальным миром и персонажами. Здесь вы найдете всю информацию о книгах серии, 
            отзывы читателей и возможность прочитать произведения онлайн.
            """)
    else:
        st.markdown("""
        Серия книг "Стеллар" - это увлекательная фантастическая сага, которая захватывает читателей 
        своим уникальным миром и персонажами. Здесь вы найдете всю информацию о книгах серии, 
        отзывы читателей и возможность прочитать произведения онлайн.
        """)
else:
    st.markdown("""
    Серия книг "Стеллар" - это увлекательная фантастическая сага, которая захватывает читателей 
    своим уникальным миром и персонажами. Здесь вы найдете всю информацию о книгах серии, 
    отзывы читателей и возможность прочитать произведения онлайн.
    """)

# Статистика
st.header("📊 Статистика")

col1, col2, col3, col4 = st.columns(4)

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
st.header("🔄 Обновление отзывов с FantLab")

col1, col2 = st.columns([3, 1])

with col1:
    st.info("Нажмите кнопку для обновления отзывов с ресурса FantLab.ru. Это может занять некоторое время.")

with col2:
    if st.button("🔄 Обновить отзывы", type="primary"):
        with st.spinner("Обновление отзывов..."):
            try:
                result = sync_reviews_from_fantlab()
                if result.get("success"):
                    total_reviews = result.get('total_reviews', 0)
                    updated_books = result.get('updated_books', 0)
                    st.success(f"✅ Обновлено {total_reviews} отзывов для {updated_books} книг")
                    if result.get('series_rating'):
                        st.info(f"⭐ Оценка цикла: {result.get('series_rating', 0):.2f}")
                    st.rerun()
                else:
                    error_msg = result.get('error', 'Неизвестная ошибка')
                    st.error(f"❌ Ошибка: {error_msg}")
                    st.info("💡 Проверьте, что у книг установлены fantlab_work_id и fantlab_series_id")
            except Exception as e:
                st.error(f"❌ Критическая ошибка: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

st.markdown("---")

# Последние отзывы
st.header("💬 Последние отзывы")

# Сортировка и фильтр
col1, col2 = st.columns([2, 2])
with col1:
    sort_option = st.selectbox(
        "Сортировка:",
        ["По дате (новые)", "По дате (старые)", "По лайкам (больше)", "По лайкам (меньше)"],
        key="main_sort"
    )
with col2:
    filter_type = st.selectbox(
        "Фильтр:",
        ["Все", "Только комментарии", "Только рецензии"],
        key="main_filter"
    )

# Получаем все отзывы
all_reviews_data = ReviewRepositorySupabase.get_all_recent(limit=100)
all_reviews = dicts_to_reviews(all_reviews_data)

# Фильтруем по типу
if filter_type == "Только комментарии":
    recent_reviews = [r for r in all_reviews if r.comment_type == "comment"]
elif filter_type == "Только рецензии":
    recent_reviews = [r for r in all_reviews if r.comment_type == "review"]
else:
    recent_reviews = all_reviews

# Сортируем
if sort_option == "По дате (новые)":
    recent_reviews.sort(key=lambda x: x.date or "", reverse=True)
elif sort_option == "По дате (старые)":
    recent_reviews.sort(key=lambda x: x.date or "")
elif sort_option == "По лайкам (больше)":
    recent_reviews.sort(key=lambda x: x.likes_count or 0, reverse=True)
elif sort_option == "По лайкам (меньше)":
    recent_reviews.sort(key=lambda x: x.likes_count or 0)

# Ограничиваем до 10
recent_reviews = recent_reviews[:10]

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
                
                # Лайки (всегда показываем, даже если 0)
                likes_count = review.likes_count if review.likes_count is not None else 0
                if likes_count > 0:
                    st.write(f"❤️ **{likes_count}** лайков")
                else:
                    st.write("❤️ 0 лайков")
                
                # Тип (комментарий или рецензия)
                if review.comment_type == "review":
                    st.caption("📄 Рецензия")
                else:
                    st.caption("💬 Комментарий")
                
                # Текст отзыва
                if review.text:
                    # Очищаем текст от возможных артефактов парсинга
                    text = review.text.strip()
                    # Удаляем фразы интерфейса, если они попали в текст
                    interface_phrases = [
                        'сортировать повремени', 'по убываниювремени', 'по возрастаниюпопулярности',
                        'сортировать по', 'по времени', 'по убыванию', 'по возрастанию'
                    ]
                    for phrase in interface_phrases:
                        text = text.replace(phrase, '').strip()
                    
                    if text and len(text) > 5:
                        st.write(text)
                    else:
                        st.write("*Отзыв без текста*")
                else:
                    st.write("*Отзыв без текста*")
            
            with col2:
                likes_count = review.likes_count if review.likes_count is not None else 0
                st.metric("❤️", likes_count)
            
            st.markdown("---")
else:
    st.info("Пока нет отзывов. Обновите отзывы с FantLab, чтобы увидеть их здесь.")
