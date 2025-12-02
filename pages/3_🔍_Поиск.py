"""Страница поиска по базе знаний."""
import streamlit as st
import os
from database.repository_supabase import BookRepositorySupabase, ReviewRepositorySupabase
from database.helpers import dict_to_book, dicts_to_books, dicts_to_reviews
from services.search import search_books
from services.fantlab_api import FantLab
from services.fb2_parser import FB2Parser
from utils.config import Config

st.title("🔍 Поиск по базе знаний")
st.markdown("---")

# Поисковая форма
col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

with col1:
    search_query = st.text_input(
        "Введите поисковый запрос:",
        placeholder="Например: название книги, автор, описание...",
        key="search_input"
    )

with col2:
    use_full_text = st.checkbox("Полнотекстовый поиск", value=True)

with col3:
    search_in_reviews = st.checkbox("Искать в рецензиях", value=False)

with col4:
    search_in_content = st.checkbox("Искать в текстах книг", value=False)

# Кнопка поиска
if st.button("🔍 Найти", type="primary") or search_query:
    if search_query and search_query.strip():
        with st.spinner("Поиск..."):
            results_data = search_books(search_query, use_full_text=use_full_text)
            results = dicts_to_books(results_data)
            
            # Если включен поиск в рецензиях
            if search_in_reviews:
                all_books_data = BookRepositorySupabase.get_all()
                query_lower = search_query.lower().strip()
                existing_ids = {r.id for r in results}
                
                for book_data in all_books_data:
                    book_id = book_data.get("id")
                    # Пропускаем, если книга уже в результатах
                    if any(r.id == book_id for r in results):
                        continue
                    
                    # Ищем в рецензиях этой книги
                    reviews_data = ReviewRepositorySupabase.get_by_book_id_and_type(book_id, "review")
                    if reviews_data:
                        for review_data in reviews_data:
                            review_text = (review_data.get("text") or "").lower()
                            if query_lower in review_text:
                                # Добавляем книгу в результаты
                                results.append(dict_to_book(book_data))
                                break
            
            # Если включен поиск в текстах книг
            if search_in_content:
                all_books_data = BookRepositorySupabase.get_all()
                query_lower = search_query.lower().strip()
                existing_ids = {r.id for r in results}
                
                for book_data in all_books_data:
                    book_id = book_data.get("id")
                    # Пропускаем, если книга уже в результатах
                    if any(r.id == book_id for r in results):
                        continue
                    
                    # Ищем в тексте книги (FB2 файл)
                    book = dict_to_book(book_data)
                    fb2_path = None
                    
                    if book.fb2_file_path:
                        if os.path.exists(book.fb2_file_path):
                            fb2_path = book.fb2_file_path
                        else:
                            full_path = os.path.join(Config.BOOKS_DIR, os.path.basename(book.fb2_file_path))
                            if os.path.exists(full_path):
                                fb2_path = full_path
                    
                    if not fb2_path:
                        books_dir = Config.BOOKS_DIR
                        if os.path.exists(books_dir):
                            for filename in os.listdir(books_dir):
                                if filename.lower().endswith('.fb2'):
                                    if book.title.lower().replace(' ', '_') in filename.lower():
                                        fb2_path = os.path.join(books_dir, filename)
                                        break
                    
                    if fb2_path and os.path.exists(fb2_path):
                        try:
                            parsed_book = FB2Parser.parse_fb2(fb2_path)
                            if "error" not in parsed_book:
                                # Ищем в тексте всех секций
                                all_text = ""
                                for section in parsed_book.get("sections", []):
                                    section_text = section.get("text", "")
                                    if section_text:
                                        all_text += section_text.lower() + " "
                                
                                if query_lower in all_text:
                                    # Добавляем книгу в результаты
                                    results.append(book)
                        except Exception:
                            pass  # Игнорируем ошибки парсинга
        
        if results:
            st.success(f"Найдено книг: {len(results)}")
            st.markdown("---")
            
            # Отображаем результаты
            for book in results:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Получаем данные с FantLab для отображения
                        book_title = book.title
                        book_author = book.author
                        book_description = book.description
                        
                        if book.fantlab_work_id:
                            try:
                                api = FantLab()
                                work_info = api.get_work_info(book.fantlab_work_id)
                                
                                if "error" not in work_info:
                                    if work_info.get("title"):
                                        book_title = work_info.get("title")
                                    if work_info.get("author"):
                                        book_author = work_info.get("author")
                                    if work_info.get("annotation"):
                                        book_description = work_info.get("annotation")
                            except Exception:
                                pass  # Используем данные из базы, если ошибка
                        
                        st.subheader(f"📖 {book_title}")
                        st.write(f"**Автор:** {book_author}")
                        
                        if book_description:
                            # Выделяем найденные слова в описании
                            description = book_description
                            if len(description) > 300:
                                description = description[:300] + "..."
                            st.write(description)
                        
                        if book.series_order:
                            st.caption(f"Порядок в серии: #{book.series_order}")
                    
                    with col2:
                        # Статистика с FantLab
                        if book.fantlab_work_id:
                            try:
                                api = FantLab()
                                work_info = api.get_work_info(book.fantlab_work_id)
                                
                                if "error" not in work_info:
                                    rating = work_info.get("rating", 0.0)
                                    voters_count = work_info.get("voters_count", 0)
                                    reviews_count = work_info.get("reviews_count", 0)
                                    
                                    if rating > 0:
                                        st.metric("⭐ Рейтинг", f"{rating:.2f}")
                                    else:
                                        st.metric("⭐ Рейтинг", "Нет данных")
                                    
                                    if voters_count > 0:
                                        st.metric("👥 Оценок", voters_count)
                                    else:
                                        st.metric("👥 Оценок", "Нет данных")
                                    
                                    st.metric("📝 Отзывов", reviews_count)
                                else:
                                    # Fallback на данные из базы
                                    st.metric("⭐ Рейтинг", book.fantlab_rating if book.fantlab_rating else "Нет данных")
                                    st.metric("👥 Оценок", book.fantlab_voters_count if book.fantlab_voters_count else 0)
                                    st.metric("📝 Отзывов", book.fantlab_reviews_count if book.fantlab_reviews_count else 0)
                            except Exception:
                                # Fallback на данные из базы
                                st.metric("⭐ Рейтинг", book.fantlab_rating if book.fantlab_rating else "Нет данных")
                                st.metric("👥 Оценок", book.fantlab_voters_count if book.fantlab_voters_count else 0)
                                st.metric("📝 Отзывов", book.fantlab_reviews_count if book.fantlab_reviews_count else 0)
                        else:
                            st.info("fantlab_work_id не установлен")
                        
                        # Кнопка перехода к книге
                        if st.button(f"Открыть", key=f"open_{book.id}"):
                            st.session_state['selected_book_id'] = book.id
                            st.switch_page("pages/2_📚_Книги")
                    
                    st.markdown("---")
        else:
            st.warning("По вашему запросу ничего не найдено. Попробуйте изменить поисковый запрос.")
    else:
        # Показываем все книги, если запрос пустой
        all_books_data = BookRepositorySupabase.get_all()
        all_books = dicts_to_books(all_books_data)
        if all_books:
            st.info(f"Всего книг в базе: {len(all_books)}")
            st.markdown("---")
            
            for book in all_books:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.subheader(f"📖 {book.title}")
                        st.write(f"**Автор:** {book.author}")
                        
                        if book.description:
                            description = book.description
                            if len(description) > 200:
                                description = description[:200] + "..."
                            st.write(description)
                    
                    with col2:
                        # Статистика с FantLab
                        if book.fantlab_work_id:
                            try:
                                api = FantLab()
                                work_info = api.get_work_info(book.fantlab_work_id)
                                
                                if "error" not in work_info:
                                    rating = work_info.get("rating", 0.0)
                                    voters_count = work_info.get("voters_count", 0)
                                    reviews_count = work_info.get("reviews_count", 0)
                                    
                                    if rating > 0:
                                        st.metric("⭐ Рейтинг", f"{rating:.2f}")
                                    else:
                                        st.metric("⭐ Рейтинг", "Нет данных")
                                    
                                    if voters_count > 0:
                                        st.metric("👥 Оценок", voters_count)
                                    else:
                                        st.metric("👥 Оценок", "Нет данных")
                                    
                                    st.metric("📝 Отзывов", reviews_count)
                                else:
                                    # Fallback на данные из базы
                                    st.metric("⭐ Рейтинг", book.fantlab_rating if book.fantlab_rating else "Нет данных")
                                    st.metric("👥 Оценок", book.fantlab_voters_count if book.fantlab_voters_count else 0)
                                    st.metric("📝 Отзывов", book.fantlab_reviews_count if book.fantlab_reviews_count else 0)
                            except Exception:
                                # Fallback на данные из базы
                                st.metric("⭐ Рейтинг", book.fantlab_rating if book.fantlab_rating else "Нет данных")
                                st.metric("👥 Оценок", book.fantlab_voters_count if book.fantlab_voters_count else 0)
                                st.metric("📝 Отзывов", book.fantlab_reviews_count if book.fantlab_reviews_count else 0)
                        else:
                            st.info("fantlab_work_id не установлен")
                        
                        if st.button(f"Открыть", key=f"view_{book.id}"):
                            st.session_state['selected_book_id'] = book.id
                            st.switch_page("pages/2_📚_Книги")
                    
                    st.markdown("---")

# Подсказки по поиску
with st.expander("💡 Подсказки по поиску"):
    st.markdown("""
    - Используйте ключевые слова из названия, имени автора или описания книги
    - Полнотекстовый поиск использует возможности PostgreSQL для более точных результатов
    - Можно искать по части слова или фразе
    - Регистр букв не имеет значения
    - Поиск в текстах книг ищет по содержимому FB2 файлов (может быть медленным)
    """)
