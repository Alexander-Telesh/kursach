"""Страница со списком всех книг с возможностью чтения и скачивания."""
import streamlit as st
import os
from datetime import datetime
from database.repository_supabase import BookRepositorySupabase, ReviewRepositorySupabase
from database.helpers import dict_to_book, dicts_to_books, dicts_to_reviews
from services.fb2_parser import FB2Parser
from services.fantlab_api import FantLab, sync_reviews_from_fantlab
from utils.config import Config

st.title("📚 Книги серии 'Стеллар'")
st.markdown("---")

# Получаем все книги (обновляем при каждом рендере для актуальности данных)
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
        # Получаем данные с FantLab для отображения
        book_title = selected_book.title
        book_author = selected_book.author
        book_description = selected_book.description
        
        if selected_book.fantlab_work_id:
            try:
                api = FantLab()
                work_info = api.get_work_info(selected_book.fantlab_work_id)
                
                if "error" not in work_info:
                    # Используем данные с FantLab, если они есть
                    if work_info.get("title"):
                        book_title = work_info.get("title")
                    if work_info.get("author"):
                        book_author = work_info.get("author")
                    if work_info.get("annotation"):
                        book_description = work_info.get("annotation")
            except Exception:
                pass  # Используем данные из базы, если ошибка
        
        st.subheader(book_title)
        st.write(f"**Автор:** {book_author}")
        
        if book_description:
            st.write("**Описание:**")
            st.write(book_description)
        
        if selected_book.series_order:
            st.caption(f"Порядок в серии: #{selected_book.series_order}")
    
    with col2:
        # Статистика с FantLab (всегда получаем свежие данные с API)
        if selected_book.fantlab_work_id:
            try:
                api = FantLab()
                work_info = api.get_work_info(selected_book.fantlab_work_id)
                
                if "error" not in work_info:
                    # Получаем свежие данные с FantLab API
                    rating = work_info.get("rating", 0.0)
                    voters_count = work_info.get("voters_count", 0)
                    reviews_count = work_info.get("reviews_count", 0)
                    
                    if rating > 0:
                        st.metric("⭐ Рейтинг", f"{rating:.2f}")
                    else:
                        st.metric("⭐ Рейтинг", "Нет данных")
                    
                    if voters_count > 0:
                        st.metric("👥 Количество оценок", voters_count)
                    else:
                        st.metric("👥 Количество оценок", "Нет данных")
                    
                    st.metric("📝 Количество отзывов", reviews_count)
                else:
                    # Fallback на данные из базы, если API недоступен
                    st.metric("⭐ Рейтинг", selected_book.fantlab_rating if selected_book.fantlab_rating else "Нет данных")
                    st.metric("👥 Количество оценок", selected_book.fantlab_voters_count if selected_book.fantlab_voters_count else 0)
                    st.metric("📝 Количество отзывов", selected_book.fantlab_reviews_count if selected_book.fantlab_reviews_count else 0)
            except Exception as e:
                # Fallback на данные из базы, если FantLab недоступен
                st.metric("⭐ Рейтинг", selected_book.fantlab_rating if selected_book.fantlab_rating else "Нет данных")
                st.metric("👥 Количество оценок", selected_book.fantlab_voters_count if selected_book.fantlab_voters_count else 0)
                st.metric("📝 Количество отзывов", selected_book.fantlab_reviews_count if selected_book.fantlab_reviews_count else 0)
        else:
            st.info("fantlab_work_id не установлен")
    
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
    
    # Информация с FantLab
    if selected_book.fantlab_work_id:
        st.header("📊 Информация с FantLab")
        
        # Сначала получаем свежие данные с FantLab API для сравнения
        api = FantLab()
        fresh_work_info = {}
        try:
            fresh_work_info = api.get_work_info(selected_book.fantlab_work_id)
        except Exception:
            pass
        
        # Проверяем, есть ли изменения на FantLab
        needs_update = False
        if "error" not in fresh_work_info:
            fresh_rating = fresh_work_info.get("rating", 0.0)
            fresh_voters = fresh_work_info.get("voters_count", 0)
            fresh_reviews = fresh_work_info.get("reviews_count", 0)
            
            cached_rating = selected_book.fantlab_rating
            cached_voters = selected_book.fantlab_voters_count or 0
            cached_reviews = selected_book.fantlab_reviews_count or 0
            
            # Проверяем изменения
            if cached_rating is not None and fresh_rating > 0:
                if abs(cached_rating - fresh_rating) > 0.01:
                    needs_update = True
            if cached_voters != fresh_voters:
                needs_update = True
            if cached_reviews != fresh_reviews:
                needs_update = True
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if needs_update:
                st.warning("⚠️ Обнаружены изменения на FantLab! Нажмите кнопку для обновления данных в базе.")
            else:
                st.info("💡 Данные обновляются автоматически при загрузке страницы. Нажмите кнопку для принудительного обновления.")
        
        with col2:
            if st.button("🔄 Обновить данные", key=f"update_fantlab_{selected_book.id}", type="primary"):
                with st.spinner("Обновление данных с FantLab..."):
                    try:
                        result = sync_reviews_from_fantlab(book_id=selected_book.id)
                        if result.get("success"):
                            reviews_count = result.get('reviews', 0)
                            rating = result.get('rating', 0.0)
                            voters_count = result.get('voters_count', 0)
                            
                            st.success(f"✅ Данные обновлены в базе!")
                            if rating > 0:
                                st.info(f"⭐ Рейтинг: {rating:.2f}")
                            if voters_count > 0:
                                st.info(f"👥 Оценок: {voters_count}")
                            if reviews_count > 0:
                                st.info(f"📝 Обновлено отзывов: {reviews_count}")
                            
                            # Перезагружаем страницу для отображения обновленных данных
                            st.rerun()
                        else:
                            st.error(f"❌ {result.get('error', 'Неизвестная ошибка')}")
                    except Exception as e:
                        st.error(f"❌ Ошибка обновления: {e}")
                        import traceback
                        st.code(traceback.format_exc())
        
        # Получаем информацию о произведении (используем уже полученные свежие данные или запрашиваем заново)
        try:
            if not fresh_work_info or "error" in fresh_work_info:
                work_info = api.get_work_info(selected_book.fantlab_work_id)
            else:
                work_info = fresh_work_info
            
            if "error" not in work_info:
                # Метрики произведения с FantLab (свежие данные с API)
                rating = work_info.get("rating", 0.0)
                voters_count = work_info.get("voters_count", 0)
                reviews_count = work_info.get("reviews_count", 0)
                title = work_info.get("title", "")
                author = work_info.get("author", "")
                
                # Основная информация
                if title:
                    st.write(f"**Название:** {title}")
                if author:
                    st.write(f"**Автор:** {author}")
                
                # Метрики в колонках (показываем свежие данные с API)
                col1, col2, col3 = st.columns(3)
                with col1:
                    if rating > 0:
                        st.metric("⭐ Рейтинг", f"{rating:.2f}")
                    else:
                        st.metric("⭐ Рейтинг", "Нет данных")
                with col2:
                    if voters_count > 0:
                        st.metric("👥 Количество оценок", voters_count)
                    else:
                        st.metric("👥 Количество оценок", "Нет данных")
                with col3:
                    st.metric("📝 Количество отзывов", reviews_count)
                
                # Показываем разницу с кэшированными данными в базе, если есть
                cached_rating = selected_book.fantlab_rating
                cached_voters = selected_book.fantlab_voters_count or 0
                cached_reviews = selected_book.fantlab_reviews_count or 0
                
                # Проверяем, есть ли изменения (с учетом возможных None значений)
                has_changes = False
                if cached_rating is not None and rating > 0:
                    if abs(cached_rating - rating) > 0.01:
                        has_changes = True
                if cached_voters != voters_count:
                    has_changes = True
                if cached_reviews != reviews_count:
                    has_changes = True
                
                if has_changes:
                    st.info("💡 Обнаружены изменения на FantLab! Нажмите '🔄 Обновить данные' для сохранения в базу.")
            else:
                # Если API недоступен, показываем кэшированные данные
                st.warning("⚠️ Не удалось получить свежие данные с FantLab. Показаны кэшированные данные.")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("⭐ Рейтинг", selected_book.fantlab_rating if selected_book.fantlab_rating else "Нет данных")
                with col2:
                    st.metric("👥 Количество оценок", selected_book.fantlab_voters_count if selected_book.fantlab_voters_count else 0)
                with col3:
                    st.metric("📝 Количество отзывов", selected_book.fantlab_reviews_count if selected_book.fantlab_reviews_count else 0)
        except Exception as e:
            st.warning(f"⚠️ Ошибка получения данных с FantLab: {e}")
            # Показываем кэшированные данные
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("⭐ Рейтинг", selected_book.fantlab_rating if selected_book.fantlab_rating else "Нет данных")
            with col2:
                st.metric("👥 Количество оценок", selected_book.fantlab_voters_count if selected_book.fantlab_voters_count else 0)
            with col3:
                st.metric("📝 Количество отзывов", selected_book.fantlab_reviews_count if selected_book.fantlab_reviews_count else 0)
    
    # Информация о цикле (если есть series_id)
    if selected_book.fantlab_series_id:
        try:
            api = FantLab()
            series_info = api.get_series_info(selected_book.fantlab_series_id)
            
            if "error" not in series_info:
                st.markdown("---")
                st.header("📚 Информация о цикле")
                
                # Название цикла
                series_title = series_info.get("title", "")
                if series_title:
                    st.write(f"**Название цикла:** {series_title}")
                
                # Аннотация цикла
                if series_info.get("annotation"):
                    with st.expander("📝 Аннотация цикла"):
                        st.write(series_info["annotation"])
                
                # Статистика цикла
                series_rating = series_info.get("rating", 0.0)
                series_reviews_count = series_info.get("reviews_count", 0)
                works_count = len(series_info.get("works", []))
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if series_rating > 0:
                        st.metric("⭐ Оценка цикла", f"{series_rating:.2f}")
                    else:
                        st.metric("⭐ Оценка цикла", "Нет данных")
                with col2:
                    st.metric("📝 Отзывов на цикл", series_reviews_count)
                with col3:
                    if works_count > 0:
                        st.metric("📚 Произведений", works_count)
        except Exception as e:
            pass  # Тихо игнорируем ошибки для цикла
    
    st.markdown("---")
    
    # Ссылки на отзывы на FantLab
    st.header("💬 Отзывы и комментарии")
    
    if selected_book.fantlab_work_id:
        fantlab_url = f"https://fantlab.ru/work/{selected_book.fantlab_work_id}#responses"
        st.info(f"📝 Отзывы и комментарии к этой книге доступны на FantLab.ru")
        st.markdown(f"[🔗 Перейти к отзывам на FantLab.ru]({fantlab_url})")
        
        # Показываем количество отзывов
        try:
            api = FantLab()
            work_info = api.get_work_info(selected_book.fantlab_work_id)
            if "error" not in work_info:
                reviews_count = work_info.get("reviews_count", 0)
                if reviews_count > 0:
                    st.success(f"✅ На FantLab.ru найдено {reviews_count} отзывов")
                else:
                    st.info("ℹ️ На FantLab.ru пока нет отзывов к этой книге")
        except Exception:
            pass
    else:
        st.warning("⚠️ Для просмотра отзывов необходимо установить fantlab_work_id для этой книги.")
