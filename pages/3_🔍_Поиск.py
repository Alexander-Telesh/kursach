"""Страница поиска по базе знаний."""
import streamlit as st
from database.repository_supabase import BookRepositorySupabase, ReviewRepositorySupabase
from database.helpers import dict_to_book, dicts_to_books
from services.search import search_books

st.title("🔍 Поиск по базе знаний")
st.markdown("---")

# Поисковая форма
col1, col2 = st.columns([4, 1])

with col1:
    search_query = st.text_input(
        "Введите поисковый запрос:",
        placeholder="Например: название книги, автор, описание...",
        key="search_input"
    )

with col2:
    use_full_text = st.checkbox("Полнотекстовый поиск", value=True)

# Кнопка поиска
if st.button("🔍 Найти", type="primary") or search_query:
    if search_query and search_query.strip():
        with st.spinner("Поиск..."):
            results_data = search_books(search_query, use_full_text=use_full_text)
            results = dicts_to_books(results_data)
        
        if results:
            st.success(f"Найдено книг: {len(results)}")
            st.markdown("---")
            
            # Отображаем результаты
            for book in results:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.subheader(f"📖 {book.title}")
                        st.write(f"**Автор:** {book.author}")
                        
                        if book.description:
                            # Выделяем найденные слова в описании
                            description = book.description
                            if len(description) > 300:
                                description = description[:300] + "..."
                            st.write(description)
                        
                        if book.series_order:
                            st.caption(f"Порядок в серии: #{book.series_order}")
                    
                    with col2:
                        # Количество комментариев и рецензий
                        comments_data = ReviewRepositorySupabase.get_by_book_id_and_type(book.id, "comment")
                        reviews_data = ReviewRepositorySupabase.get_by_book_id_and_type(book.id, "review")
                        total_likes = ReviewRepositorySupabase.get_total_likes_for_book(book.id)
                        
                        st.metric("Комментариев", len(comments_data) if comments_data else 0)
                        st.metric("Рецензий", len(reviews_data) if reviews_data else 0)
                        if total_likes > 0:
                            st.metric("Лайков", total_likes)
                        
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
                        # Количество комментариев и рецензий
                        comments_data = ReviewRepositorySupabase.get_by_book_id_and_type(book.id, "comment")
                        reviews_data = ReviewRepositorySupabase.get_by_book_id_and_type(book.id, "review")
                        total_likes = ReviewRepositorySupabase.get_total_likes_for_book(book.id)
                        
                        st.metric("Комментариев", len(comments_data) if comments_data else 0)
                        st.metric("Рецензий", len(reviews_data) if reviews_data else 0)
                        if total_likes > 0:
                            st.metric("Лайков", total_likes)
                        
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
    """)
