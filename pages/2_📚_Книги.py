"""Страница со списком всех книг с возможностью чтения и скачивания."""
import streamlit as st
import os
from database.repository_supabase import BookRepositorySupabase, ReviewRepositorySupabase
from database.helpers import dict_to_book, dicts_to_books, dicts_to_reviews
from services.fb2_parser import FB2Parser
from utils.config import Config

st.title("📚 Книги серии 'Стеллар'")
st.markdown("---")

# Получаем все книги
books_data = BookRepositorySupabase.get_all()
books = dicts_to_books(books_data)

# Проверяем, есть ли выбранная книга из поиска
selected_book_id = st.session_state.get('selected_book_id', None)
initial_index = 0
if selected_book_id and books:
    # Находим индекс выбранной книги
    for i, book in enumerate(books):
        if book.id == selected_book_id:
            initial_index = i
            break
    # Очищаем выбранную книгу из session_state после использования
    if 'selected_book_id' in st.session_state:
        del st.session_state['selected_book_id']

if not books:
    st.warning("В базе данных пока нет книг. Добавьте книги через админ-панель или напрямую в базу данных.")
    st.info("Для добавления книг создайте записи в таблице 'books' в Supabase.")
else:
    # Список книг
    st.header("📖 Список книг")
    
    # Выбор книги
    book_titles = [f"{book.title} - {book.author}" for book in books]
    current_index = st.selectbox(
        "Выберите книгу для чтения:",
        range(len(book_titles)),
        format_func=lambda x: book_titles[x],
        index=initial_index
    )
    
    selected_book = books[current_index]
    
    st.markdown("---")
    
    # Информация о выбранной книге
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(selected_book.title)
        st.write(f"**Автор:** {selected_book.author}")
        
        if selected_book.description:
            st.write("**Описание:**")
            st.write(selected_book.description)
        
        if selected_book.series_order:
            st.caption(f"Порядок в серии: #{selected_book.series_order}")
    
    with col2:
        # Средний рейтинг книги
        avg_rating = ReviewRepositorySupabase.get_average_rating(selected_book.id)
        if avg_rating:
            st.metric("Средний рейтинг", f"{avg_rating:.2f} ⭐")
        
        # Количество отзывов
        reviews_data = ReviewRepositorySupabase.get_by_book_id(selected_book.id)
        st.metric("Отзывов", len(reviews_data))
    
    st.markdown("---")
    
    # Чтение книги
    st.header("📖 Чтение книги")
    
    # Проверяем наличие FB2 файла
    fb2_path = None
    
    if selected_book.fb2_file_path:
        # Используем путь из базы данных
        if os.path.exists(selected_book.fb2_file_path):
            fb2_path = selected_book.fb2_file_path
        else:
            # Пробуем относительный путь
            full_path = os.path.join(Config.BOOKS_DIR, os.path.basename(selected_book.fb2_file_path))
            if os.path.exists(full_path):
                fb2_path = full_path
    
    # Если путь не указан, ищем файл по названию
    if not fb2_path:
        books_dir = Config.BOOKS_DIR
        if os.path.exists(books_dir):
            # Ищем FB2 файлы, которые могут соответствовать книге
            for filename in os.listdir(books_dir):
                if filename.lower().endswith('.fb2'):
                    # Простая проверка по названию (можно улучшить)
                    if selected_book.title.lower().replace(' ', '_') in filename.lower():
                        fb2_path = os.path.join(books_dir, filename)
                        break
    
    if fb2_path and os.path.exists(fb2_path):
        # Кнопка скачивания
        with open(fb2_path, 'rb') as f:
            st.download_button(
                label="⬇️ Скачать книгу (FB2)",
                data=f.read(),
                file_name=os.path.basename(fb2_path),
                mime="application/xml"
            )
        
        st.markdown("---")
        
        # Парсим и отображаем книгу
        parsed_book = FB2Parser.parse_fb2(fb2_path)
        
        if parsed_book.get("sections"):
            st.subheader("Содержание:")
            for i, section in enumerate(parsed_book["sections"]):
                with st.expander(f"📄 {section.get('title', f'Глава {i+1}')}" if section.get('title') else f"📄 Глава {i+1}"):
                    if section.get("text"):
                        st.markdown(section["text"].replace('\n', '\n\n'))
        else:
            st.info("Не удалось извлечь содержимое из FB2 файла.")
    else:
        st.warning("FB2 файл для этой книги не найден.")
        st.info(f"Ожидаемый путь: {selected_book.fb2_file_path or 'не указан'}")
        st.info(f"Папка с книгами: {Config.BOOKS_DIR}")
        
        # Показываем список доступных FB2 файлов
        available_files = FB2Parser.get_fb2_files()
        if available_files:
            st.write("**Доступные FB2 файлы:**")
            for file_path in available_files:
                st.write(f"- {os.path.basename(file_path)}")
    
    st.markdown("---")
    
    # Отзывы на книгу
    st.header("💬 Отзывы на книгу")
    book_reviews_data = ReviewRepositorySupabase.get_by_book_id(selected_book.id)
    book_reviews = dicts_to_reviews(book_reviews_data)
    
    if book_reviews:
        for review in book_reviews:
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
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
                    
                    if review.rating:
                        stars = "⭐" * int(review.rating)
                        st.write(f"**Оценка:** {review.rating:.1f} {stars}")
                    
                    if review.text:
                        st.write(review.text)
                    else:
                        st.write("*Отзыв без текста*")
                
                with col2:
                    if review.rating:
                        st.metric("", f"{review.rating:.1f}")
                
                st.markdown("---")
    else:
        st.info("Пока нет отзывов на эту книгу. Обновите отзывы с AuthorToday на главной странице.")
