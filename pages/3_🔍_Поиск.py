"""Страница поиска по базе знаний."""
import streamlit as st
import os
from database.repository_supabase import BookRepositorySupabase
from database.helpers import dict_to_book, dicts_to_books
from services.search import search_books
from services.fantlab_api import FantLab
from services.fb2_parser import FB2Parser
from utils.config import Config

st.title("🔍 Поиск по базе знаний")
st.markdown("---")

# Поисковая форма
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    search_query = st.text_input(
        "Введите поисковый запрос:",
        placeholder="Например: название книги, автор, описание...",
        key="search_input"
    )

with col2:
    use_full_text = st.checkbox("Полнотекстовый поиск", value=True)

with col3:
    search_in_content = st.checkbox("Искать в текстах книг", value=False)

# Кнопка поиска
if st.button("🔍 Найти", type="primary") or search_query:
    if search_query and search_query.strip():
        with st.spinner("Поиск..."):
            results_data = search_books(search_query, use_full_text=use_full_text)
            results = dicts_to_books(results_data)
            
            # Если включен поиск в текстах книг
            # Сохраняем контексты найденных совпадений
            book_matches = {}  # {book_id: [{"section_title": "...", "context": "...", "position": ...}, ...]}
            
            if search_in_content:
                all_books_data = BookRepositorySupabase.get_all()
                query_lower = search_query.lower().strip()
                query_original = search_query.strip()
                existing_ids = {r.id for r in results}
                
                for book_data in all_books_data:
                    book_id = book_data.get("id")
                    book = dict_to_book(book_data)
                    
                    # Пропускаем, если книга уже в результатах
                    if any(r.id == book_id for r in results):
                        continue
                    
                    # Ищем в тексте книги (FB2 файл)
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
                                matches = []
                                
                                # Ищем в тексте всех секций
                                for section in parsed_book.get("sections", []):
                                    section_title = section.get("title", "")
                                    section_text = section.get("text", "")
                                    
                                    if section_text:
                                        # Ищем совпадения (поддерживаем и точные фразы, и отдельные слова)
                                        text_lower = section_text.lower()
                                        
                                        # Проверяем точное совпадение фразы
                                        if query_lower in text_lower:
                                            # Находим все позиции совпадений
                                            start_pos = 0
                                            while True:
                                                pos = text_lower.find(query_lower, start_pos)
                                                if pos == -1:
                                                    break
                                                
                                                # Извлекаем контекст (150 символов до и после)
                                                context_start = max(0, pos - 150)
                                                context_end = min(len(section_text), pos + len(query_original) + 150)
                                                context = section_text[context_start:context_end]
                                                
                                                # Выделяем найденный текст (используем markdown для выделения)
                                                match_in_context = pos - context_start
                                                match_text = context[match_in_context:match_in_context + len(query_original)]
                                                highlighted_context = (
                                                    context[:match_in_context] +
                                                    f"**{match_text}**" +
                                                    context[match_in_context + len(query_original):]
                                                )
                                                
                                                matches.append({
                                                    "section_title": section_title or "Без названия",
                                                    "context": highlighted_context,
                                                    "position": pos
                                                })
                                                
                                                start_pos = pos + 1
                                        
                                        # Если точное совпадение не найдено, ищем по отдельным словам
                                        elif len(query_lower.split()) > 1:
                                            query_words = query_lower.split()
                                            # Проверяем, что все слова присутствуют в тексте
                                            if all(word in text_lower for word in query_words):
                                                # Находим позицию первого слова
                                                first_word_pos = text_lower.find(query_words[0])
                                                if first_word_pos != -1:
                                                    # Извлекаем контекст вокруг первого слова
                                                    context_start = max(0, first_word_pos - 150)
                                                    context_end = min(len(section_text), first_word_pos + 200)
                                                    context = section_text[context_start:context_end]
                                                    
                                                    # Выделяем все найденные слова в оригинальном контексте
                                                    highlighted_context = context
                                                    context_lower = context.lower()
                                                    
                                                    # Выделяем слова в обратном порядке, чтобы позиции не сдвигались
                                                    for word in reversed(query_words):
                                                        word_lower = word.lower()
                                                        # Ищем слово в оригинальном контексте
                                                        word_pos = context_lower.find(word_lower)
                                                        if word_pos != -1:
                                                            # Находим границы слова (учитываем только буквы и цифры)
                                                            word_start = word_pos
                                                            word_end = word_pos + len(word)
                                                            
                                                            # Расширяем границы до полного слова
                                                            while word_start > 0 and context[word_start-1].isalnum():
                                                                word_start -= 1
                                                            while word_end < len(context) and context[word_end].isalnum():
                                                                word_end += 1
                                                            
                                                            if word_end > word_start:
                                                                word_text = context[word_start:word_end]
                                                                highlighted_context = (
                                                                    highlighted_context[:word_start] +
                                                                    f"**{word_text}**" +
                                                                    highlighted_context[word_end:]
                                                                )
                                                    
                                                    matches.append({
                                                        "section_title": section_title or "Без названия",
                                                        "context": highlighted_context,
                                                        "position": first_word_pos
                                                    })
                                
                                if matches:
                                    # Добавляем книгу в результаты
                                    results.append(book)
                                    book_matches[book_id] = matches
                        except Exception as e:
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
                        
                        # Показываем найденные совпадения в тексте книги
                        if search_in_content and book.id in book_matches:
                            st.markdown("**🔍 Найдено в тексте книги:**")
                            matches = book_matches[book.id]
                            # Показываем первые 3 совпадения
                            for i, match in enumerate(matches[:3]):
                                with st.expander(f"📄 {match['section_title']} (совпадение {i+1})"):
                                    st.markdown(f"...{match['context']}...")
                            if len(matches) > 3:
                                st.caption(f"И еще {len(matches) - 3} совпадений...")
                        
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
    - Поиск в текстах книг ищет по содержимому FB2 файлов и показывает контекст найденных совпадений
    - При поиске в текстах книг отображаются фрагменты текста с выделенными совпадениями
    """)
