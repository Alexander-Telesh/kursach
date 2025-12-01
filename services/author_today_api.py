"""Интеграция с AuthorToday API для получения отзывов."""
import requests
import time
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from utils.config import Config


class AuthorToday:
    """Класс для работы с AuthorToday API."""
    
    def __init__(self):
        self.api = Config.AUTHORTODAY_API_URL or "https://api.author.today"
        self.web_api = Config.AUTHORTODAY_WEB_URL or "https://author.today"
        self.token = "Bearer guest"
        self.user_id = None
        self.headers = {
            "authorization": self.token,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
            "Content-Type": "application/json"
        }
    
    def login(self, login: str, password: str) -> dict:
        """
        Авторизация в AuthorToday.
        
        Args:
            login: Логин пользователя
            password: Пароль пользователя
        
        Returns:
            Ответ от API
        """
        data = {
            "login": login,
            "password": password
        }
        
        try:
            response = requests.post(
                f"{self.api}/v1/account/login-by-password",
                json=data,
                headers=self.headers,
                timeout=10
            ).json()
            
            if "token" in response:
                self.token = response["token"]
                self.headers["authorization"] = f"Bearer {self.token}"
                account_info = self.get_account_info()
                if "id" in account_info:
                    self.user_id = account_info["id"]
            
            return response
        except Exception as e:
            print(f"❌ Ошибка авторизации в AuthorToday: {e}")
            return {"error": str(e)}
    
    def login_with_token(self, token: str) -> dict:
        """Авторизация с использованием токена."""
        self.token = token
        self.headers["authorization"] = f"Bearer {self.token}"
        response = self.get_account_info()
        if "id" in response:
            self.user_id = response["id"]
        return response
    
    def get_account_info(self) -> dict:
        """Получить информацию о текущем пользователе."""
        try:
            return requests.get(
                f"{self.api}/v1/account/current-user",
                headers=self.headers,
                timeout=10
            ).json()
        except Exception as e:
            print(f"❌ Ошибка получения информации о пользователе: {e}")
            return {"error": str(e)}
    
    def search_work(self, query: str) -> List[Dict]:
        """
        Поиск произведений по запросу через API.
        
        Args:
            query: Поисковый запрос (название книги, автор)
        
        Returns:
            Список найденных произведений
        """
        import urllib.parse
        
        # Кодируем запрос для URL
        encoded_query = urllib.parse.quote(query)
        
        # Пробуем разные варианты endpoints
        possible_endpoints = [
            f"{self.api}/v1/work/search?query={encoded_query}",
            f"{self.api}/v1/work/search?q={encoded_query}",
            f"{self.web_api}/search?q={encoded_query}",
        ]
        
        for endpoint in possible_endpoints:
            try:
                response = requests.get(
                    endpoint,
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Структура ответа может быть разной
                    if isinstance(data, dict):
                        # Пробуем разные ключи
                        items = (
                            data.get("items") or 
                            data.get("works") or 
                            data.get("data") or 
                            data.get("results") or
                            []
                        )
                        if items:
                            print(f"   ✅ Найдено через endpoint: {endpoint}")
                            return items if isinstance(items, list) else []
                    elif isinstance(data, list):
                        print(f"   ✅ Найдено через endpoint: {endpoint}")
                        return data
                elif response.status_code != 404:
                    print(f"   ⚠️  Статус {response.status_code} для {endpoint}")
            except Exception as e:
                print(f"   ⚠️  Ошибка для {endpoint}: {e}")
                continue
        
        return []
    
    def get_work_meta_info(self, work_id: int) -> dict:
        """
        Получить метаинформацию о произведении.
        
        Args:
            work_id: ID произведения в AuthorToday
        
        Returns:
            Метаинформация о произведении
        """
        try:
            return requests.get(
                f"{self.api}/v1/work/{work_id}/meta-info",
                headers=self.headers,
                timeout=10
            ).json()
        except Exception as e:
            print(f"❌ Ошибка получения информации о произведении: {e}")
            return {"error": str(e)}
    
    def get_work_info(self, work_id: int) -> Dict:
        """
        Получить полную информацию о работе с веб-страницы AuthorToday.
        Включает аннотацию и статистику.
        
        Args:
            work_id: ID произведения в AuthorToday
        
        Returns:
            Словарь с информацией: annotation, statistics (views, reads, subscribers, etc.)
        """
        try:
            url = f"{self.web_api}/work/{work_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}"}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            result = {
                "annotation": "",
                "statistics": {}
            }
            
            # Парсим аннотацию
            # Ищем блок с аннотацией (может быть в разных местах)
            annotation_selectors = [
                '.work-annotation',
                '.annotation',
                '[class*="annotation"]',
                '[class*="description"]',
                '.work-description'
            ]
            
            for selector in annotation_selectors:
                annotation_elem = soup.select_one(selector)
                if annotation_elem:
                    result["annotation"] = annotation_elem.get_text(strip=True)
                    break
            
            # Парсим статистику
            # Ищем блоки со статистикой (просмотры, чтения, подписчики, лайки)
            stats_selectors = [
                '.work-stats',
                '.statistics',
                '[class*="stat"]',
                '[class*="metric"]'
            ]
            
            for selector in stats_selectors:
                stats_elem = soup.select_one(selector)
                if stats_elem:
                    # Пытаемся извлечь числа из текста
                    text = stats_elem.get_text()
                    # Простой парсинг (можно улучшить)
                    if "просмотр" in text.lower() or "view" in text.lower():
                        # Извлекаем число просмотров
                        pass
                    break
            
            # Альтернативный способ: ищем через API meta-info
            meta_info = self.get_work_meta_info(work_id)
            if "error" not in meta_info:
                # Дополняем данными из API
                if not result["annotation"] and "annotation" in meta_info:
                    result["annotation"] = meta_info.get("annotation", "")
                
                # Статистика из API
                if "statistics" in meta_info:
                    result["statistics"] = meta_info["statistics"]
                elif "views" in meta_info or "reads" in meta_info:
                    result["statistics"] = {
                        "views": meta_info.get("views", 0),
                        "reads": meta_info.get("reads", 0),
                        "subscribers": meta_info.get("subscribers", 0),
                        "likes": meta_info.get("likes", 0)
                    }
            
            return result
        except Exception as e:
            print(f"❌ Ошибка получения информации о работе {work_id}: {e}")
            return {"error": str(e)}
    
    def get_work_likes(self, work_id: int) -> int:
        """
        Получить количество лайков у произведения.
        
        Args:
            work_id: ID произведения в AuthorToday
        
        Returns:
            Количество лайков
        """
        try:
            # Пробуем через API
            meta_info = self.get_work_meta_info(work_id)
            if "error" not in meta_info:
                likes = meta_info.get("likes") or meta_info.get("likesCount") or meta_info.get("likeCount")
                if likes is not None:
                    return int(likes)
            
            # Пробуем через веб-страницу
            url = f"{self.web_api}/work/{work_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Ищем элемент с лайками
                like_selectors = [
                    '[class*="like"]',
                    '[class*="favorite"]',
                    '[data-likes]',
                    '[data-like-count]'
                ]
                
                for selector in like_selectors:
                    like_elem = soup.select_one(selector)
                    if like_elem:
                        # Пытаемся извлечь число
                        text = like_elem.get_text()
                        # Простой парсинг числа
                        import re
                        numbers = re.findall(r'\d+', text)
                        if numbers:
                            return int(numbers[0])
                        
                        # Пробуем data-атрибут
                        likes = like_elem.get('data-likes') or like_elem.get('data-like-count')
                        if likes:
                            return int(likes)
            
            return 0
        except Exception as e:
            print(f"❌ Ошибка получения лайков для работы {work_id}: {e}")
            return 0
    
    def get_work_comments(self, work_id: int) -> List[Dict]:
        """
        Получить комментарии к произведению.
        
        Args:
            work_id: ID произведения в AuthorToday
        
        Returns:
            Список комментариев с полями: id, author_name, text, date, likes_count
        """
        comments = []
        
        # Пробуем через API
        possible_endpoints = [
            f"{self.api}/v1/work/{work_id}/comments",
            f"{self.web_api}/work/{work_id}/comments",
        ]
        
        for endpoint in possible_endpoints:
            try:
                response = requests.get(endpoint, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        comments = data
                        break
                    elif isinstance(data, dict):
                        items = data.get("comments", data.get("items", data.get("data", [])))
                        if items:
                            comments = items
                            break
            except Exception:
                continue
        
        # Если API не работает, пробуем парсинг веб-страницы
        if not comments:
            try:
                url = f"{self.web_api}/work/{work_id}"
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Пробуем разные селекторы для комментариев
                    comment_selectors = [
                        '.comment-item',
                        '.comment',
                        '[data-comment-id]',
                        '[class*="Comment"]',
                        '[class*="comment"]',
                        'div[class*="comment"]'
                    ]
                    
                    comment_elements = []
                    for selector in comment_selectors:
                        elements = soup.select(selector)
                        if elements:
                            comment_elements = elements
                            break
                    
                    for elem in comment_elements:
                        try:
                            # Извлекаем ID
                            comment_id = (
                                elem.get('data-comment-id') or 
                                elem.get('data-id') or 
                                elem.get('id') or
                                elem.get('data-commentId') or
                                ""
                            )
                            
                            # Извлекаем текст комментария
                            # Исключаем элементы интерфейса (селекторы, кнопки, навигацию)
                            excluded_selectors = [
                                'select', 'option', 'button', '.sort', '.filter',
                                '[class*="sort"]', '[class*="filter"]', '[class*="dropdown"]',
                                'nav', '.navigation', '.pagination'
                            ]
                            
                            # Удаляем элементы интерфейса перед извлечением текста
                            elem_copy = BeautifulSoup(str(elem), 'html.parser')
                            for excl_sel in excluded_selectors:
                                for excl_elem in elem_copy.select(excl_sel):
                                    excl_elem.decompose()
                            
                            text_elem = elem_copy.select_one('.comment-text, .text, [class*="text"], [class*="content"]')
                            text = text_elem.get_text(strip=True) if text_elem else elem_copy.get_text(strip=True)
                            
                            # Фильтруем текст от фраз интерфейса
                            interface_phrases = [
                                'сортировать', 'по времени', 'по убыванию', 'по возрастанию',
                                'популярности', 'сортировка', 'фильтр', 'выбрать'
                            ]
                            text_lower = text.lower()
                            for phrase in interface_phrases:
                                if phrase in text_lower and len(text) < 200:  # Короткие тексты с фразами интерфейса - пропускаем
                                    text = ""
                                    break
                            
                            # Извлекаем автора
                            author_elem = elem.select_one(
                                '.author, .user-name, .username, [class*="author"], [class*="user"], [class*="name"]'
                            )
                            author_name = author_elem.get_text(strip=True) if author_elem else "Анонимный читатель"
                            
                            # Извлекаем дату
                            date_elem = elem.select_one('.date, .time, [class*="date"], [class*="time"]')
                            date_str = date_elem.get_text(strip=True) if date_elem else None
                            
                            # Извлекаем лайки
                            likes_elem = elem.select_one(
                                '.likes, .like-count, [class*="like"], [data-likes], [data-like-count]'
                            )
                            likes_count = 0
                            if likes_elem:
                                likes_text = likes_elem.get_text(strip=True)
                                import re
                                numbers = re.findall(r'\d+', likes_text)
                                if numbers:
                                    likes_count = int(numbers[0])
                                else:
                                    likes_attr = likes_elem.get('data-likes') or likes_elem.get('data-like-count')
                                    if likes_attr:
                                        likes_count = int(likes_attr)
                            
                            if text and len(text) > 5:  # Минимальная длина комментария
                                comment = {
                                    "id": str(comment_id) if comment_id else f"comment_{len(comments)}",
                                    "author_name": author_name,
                                    "text": text,
                                    "date": date_str,
                                    "likes_count": likes_count
                                }
                                comments.append(comment)
                        except Exception as e:
                            print(f"⚠️  Ошибка обработки элемента комментария: {e}")
                            continue
                    
                    print(f"   📝 Парсинг веб-страницы: найдено {len(comments)} комментариев")
            except Exception as e:
                print(f"⚠️  Ошибка парсинга комментариев: {e}")
        
        return comments
    
    def get_work_reviews(self, work_id: int) -> List[Dict]:
        """
        Получить рецензии на произведение (отдельно от комментариев).
        
        Args:
            work_id: ID произведения в AuthorToday
        
        Returns:
            Список рецензий с полями: id, author_name, text, date, likes_count
        """
        reviews = []
        
        # Пробуем через API
        possible_endpoints = [
            f"{self.api}/v1/work/{work_id}/reviews",
            f"{self.web_api}/work/{work_id}/reviews",
        ]
        
        for endpoint in possible_endpoints:
            try:
                response = requests.get(endpoint, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        reviews = data
                        break
                    elif isinstance(data, dict):
                        items = data.get("reviews", data.get("items", data.get("data", [])))
                        if items:
                            reviews = items
                            break
            except Exception:
                continue
        
        # Если API не работает, пробуем парсинг веб-страницы
        if not reviews:
            try:
                url = f"{self.web_api}/work/{work_id}"
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Пробуем разные селекторы для рецензий
                    review_selectors = [
                        '.review-item',
                        '.review',
                        '[data-review-id]',
                        '[class*="Review"]',
                        '[class*="review"]',
                        'div[class*="review"]'
                    ]
                    
                    review_elements = []
                    for selector in review_selectors:
                        elements = soup.select(selector)
                        if elements:
                            review_elements = elements
                            break
                    
                    for elem in review_elements:
                        try:
                            # Извлекаем ID
                            review_id = (
                                elem.get('data-review-id') or 
                                elem.get('data-id') or 
                                elem.get('id') or
                                elem.get('data-reviewId') or
                                ""
                            )
                            
                            # Извлекаем текст рецензии
                            # Исключаем элементы интерфейса
                            excluded_selectors = [
                                'select', 'option', 'button', '.sort', '.filter',
                                '[class*="sort"]', '[class*="filter"]', '[class*="dropdown"]',
                                'nav', '.navigation', '.pagination'
                            ]
                            
                            # Удаляем элементы интерфейса перед извлечением текста
                            elem_copy = BeautifulSoup(str(elem), 'html.parser')
                            for excl_sel in excluded_selectors:
                                for excl_elem in elem_copy.select(excl_sel):
                                    excl_elem.decompose()
                            
                            text_elem = elem_copy.select_one('.review-text, .text, [class*="text"], [class*="content"]')
                            text = text_elem.get_text(strip=True) if text_elem else elem_copy.get_text(strip=True)
                            
                            # Фильтруем текст от фраз интерфейса
                            interface_phrases = [
                                'сортировать', 'по времени', 'по убыванию', 'по возрастанию',
                                'популярности', 'сортировка', 'фильтр', 'выбрать'
                            ]
                            text_lower = text.lower()
                            for phrase in interface_phrases:
                                if phrase in text_lower and len(text) < 200:
                                    text = ""
                                    break
                            
                            # Рецензии обычно длиннее комментариев - проверяем длину
                            if len(text) < 100:  # Пропускаем короткие тексты (это скорее комментарии)
                                continue
                            
                            # Извлекаем автора
                            author_elem = elem.select_one(
                                '.author, .user-name, .username, [class*="author"], [class*="user"], [class*="name"]'
                            )
                            author_name = author_elem.get_text(strip=True) if author_elem else "Анонимный читатель"
                            
                            # Извлекаем дату
                            date_elem = elem.select_one('.date, .time, [class*="date"], [class*="time"]')
                            date_str = date_elem.get_text(strip=True) if date_elem else None
                            
                            # Извлекаем лайки
                            likes_elem = elem.select_one(
                                '.likes, .like-count, [class*="like"], [data-likes], [data-like-count]'
                            )
                            likes_count = 0
                            if likes_elem:
                                likes_text = likes_elem.get_text(strip=True)
                                import re
                                numbers = re.findall(r'\d+', likes_text)
                                if numbers:
                                    likes_count = int(numbers[0])
                                else:
                                    likes_attr = likes_elem.get('data-likes') or likes_elem.get('data-like-count')
                                    if likes_attr:
                                        likes_count = int(likes_attr)
                            
                            if text and len(text) > 50:  # Минимальная длина рецензии
                                review = {
                                    "id": str(review_id) if review_id else f"review_{len(reviews)}",
                                    "author_name": author_name,
                                    "text": text,
                                    "date": date_str,
                                    "likes_count": likes_count
                                }
                                reviews.append(review)
                        except Exception as e:
                            print(f"⚠️  Ошибка обработки элемента рецензии: {e}")
                            continue
                    
                    print(f"   📄 Парсинг веб-страницы: найдено {len(reviews)} рецензий")
            except Exception as e:
                print(f"⚠️  Ошибка парсинга рецензий: {e}")
        
        return reviews
    
    def search_book_and_get_reviews(self, book_title: str, author_name: str = None) -> List[Dict]:
        """
        Найти книгу по названию и получить отзывы.
        
        Args:
            book_title: Название книги
            author_name: Имя автора (опционально, для уточнения поиска)
        
        Returns:
            Список отзывов
        """
        # Формируем поисковый запрос
        search_query = book_title
        if author_name:
            search_query = f"{book_title} {author_name}"
        
        # Ищем произведения через API
        works = self.search_work(search_query)
        
        if not works:
            print(f"⚠️  Книга '{book_title}' не найдена на AuthorToday")
            return []
        
        all_reviews = []
        
        # Для каждого найденного произведения получаем отзывы
        for work in works[:3]:  # Ограничиваем до 3 результатов
            # Пытаемся получить ID произведения из разных возможных полей
            work_id = work.get("id") or work.get("workId") or work.get("work_id") or work.get("Id")
            
            if not work_id:
                continue
            
            # Проверяем, что это нужная книга (по названию и автору)
            work_title = (work.get("title") or work.get("Title") or "").lower()
            work_author = (work.get("authorName") or work.get("author") or work.get("AuthorName") or "").lower()
            
            book_title_lower = book_title.lower()
            author_name_lower = (author_name or "").lower()
            
            # Проверяем совпадение названия
            title_match = (
                book_title_lower in work_title or 
                work_title in book_title_lower or
                any(word in work_title for word in book_title_lower.split() if len(word) > 3)
            )
            
            # Проверяем совпадение автора (если указан)
            author_match = True
            if author_name_lower:
                author_match = (
                    author_name_lower in work_author or 
                    work_author in author_name_lower or
                    any(word in work_author for word in author_name_lower.split() if len(word) > 3)
                )
            
            if title_match and author_match:
                print(f"📖 Найдена книга: {work.get('title', work.get('Title', 'Без названия'))} (ID: {work_id})")
                reviews = self.get_work_reviews(work_id)
                if reviews:
                    print(f"   ✅ Найдено отзывов: {len(reviews)}")
                    all_reviews.extend(reviews)
                else:
                    print(f"   ⚠️  Отзывы не найдены")
                time.sleep(0.5)  # Задержка между запросами
        
        return all_reviews


def _parse_date(date_str: Optional[str]):
    """Парсинг даты из различных форматов."""
    if not date_str:
        return None
    
    try:
        # Пробуем ISO формат
        if "T" in str(date_str):
            return datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        # Другие форматы можно добавить при необходимости
    except:
        pass
    
    return None


def sync_reviews_from_author_today(book_id: Optional[int] = None, update_likes_only: bool = False) -> Dict:
    """
    Синхронизировать комментарии, рецензии и лайки с AuthorToday.
    
    Args:
        book_id: ID книги (если None, обновляются все книги)
        update_likes_only: Если True, обновляются только лайки существующих записей
    
    Returns:
        Словарь со статистикой обновления
    """
    from database.repository_supabase import BookRepositorySupabase, ReviewRepositorySupabase
    
    # Получаем учетные данные из конфигурации
    login = Config.AUTHORTODAY_LOGIN
    password = Config.AUTHORTODAY_PASSWORD
    
    if not login or not password:
        return {
            "success": False,
            "error": "AUTHORTODAY_LOGIN и AUTHORTODAY_PASSWORD должны быть установлены в .env файле или Streamlit secrets",
            "message": "Настройте учетные данные AuthorToday в .env файле или Streamlit secrets"
        }
    
    # Создаем экземпляр API и авторизуемся
    api = AuthorToday()
    print(f"🔐 Попытка авторизации в AuthorToday для пользователя: {login}")
    login_result = api.login(login, password)
    
    if "error" in login_result:
        error_msg = login_result.get("error", "Неизвестная ошибка")
        return {
            "success": False,
            "error": f"Ошибка авторизации в AuthorToday: {error_msg}",
            "message": "Проверьте правильность логина и пароля"
        }
    
    if "token" not in login_result:
        return {
            "success": False,
            "error": "Ошибка авторизации в AuthorToday: токен не получен",
            "message": f"Ответ от API: {login_result}",
            "details": login_result
        }
    
    print(f"✅ Авторизация успешна, токен получен")
    
    def process_book(book_data: Dict) -> Dict:
        """Обработать одну книгу."""
        book_id = book_data.get("id")
        book_title = book_data.get("title", "")
        work_id = book_data.get("author_today_work_id")
        
        if not work_id:
            return {
                "book_id": book_id,
                "comments": 0,
                "reviews": 0,
                "likes_updated": 0,
                "error": "author_today_work_id не установлен"
            }
        
        print(f"📖 Обработка: '{book_title}' (work_id: {work_id})")
        
        stats = {
            "book_id": book_id,
            "comments": 0,
            "reviews": 0,
            "likes_updated": 0
        }
        
        if not update_likes_only:
            # Получаем комментарии
            comments = api.get_work_comments(work_id)
            print(f"   📝 Найдено комментариев: {len(comments)}")
            
            for comment_data in comments:
                comment_dict = {
                    "book_id": book_id,
                    "litres_review_id": str(comment_data.get("id", comment_data.get("commentId", ""))),
                    "comment_type": "comment",
                    "author_name": (
                        comment_data.get("author_name") or
                        comment_data.get("author") or 
                        comment_data.get("userName") or 
                        comment_data.get("authorName") or 
                        comment_data.get("user") or
                        "Анонимный читатель"
                    ),
                    "text": (
                        comment_data.get("text") or 
                        comment_data.get("content") or 
                        comment_data.get("comment") or 
                        comment_data.get("message") or
                        ""
                    ),
                    "likes_count": int(comment_data.get("likes_count", comment_data.get("likes", 0)) or 0),
                    "date": _parse_date(
                        comment_data.get("date") or 
                        comment_data.get("createdAt") or 
                        comment_data.get("created_at") or
                        comment_data.get("dateCreated")
                    )
                }
                
                if comment_dict["text"] and len(comment_dict["text"].strip()) > 0:
                    try:
                        ReviewRepositorySupabase.create_or_update(comment_dict)
                        stats["comments"] += 1
                        print(f"      ✅ Сохранен комментарий от {comment_dict['author_name']}")
                    except Exception as e:
                        print(f"   ⚠️  Ошибка при сохранении комментария: {e}")
                        import traceback
                        traceback.print_exc()
            
            # Получаем рецензии
            reviews = api.get_work_reviews(work_id)
            print(f"   📄 Найдено рецензий: {len(reviews)}")
            
            for review_data in reviews:
                review_dict = {
                    "book_id": book_id,
                    "litres_review_id": str(review_data.get("id", review_data.get("reviewId", ""))),
                    "comment_type": "review",
                    "author_name": (
                        review_data.get("author_name") or
                        review_data.get("author") or 
                        review_data.get("userName") or 
                        review_data.get("authorName") or 
                        review_data.get("user") or
                        "Анонимный читатель"
                    ),
                    "text": (
                        review_data.get("text") or 
                        review_data.get("content") or 
                        review_data.get("reviewText") or
                        review_data.get("message") or
                        ""
                    ),
                    "likes_count": int(review_data.get("likes_count", review_data.get("likes", 0)) or 0),
                    "date": _parse_date(
                        review_data.get("date") or 
                        review_data.get("createdAt") or 
                        review_data.get("created_at") or
                        review_data.get("dateCreated")
                    )
                }
                
                if review_dict["text"] and len(review_dict["text"].strip()) > 0:
                    try:
                        ReviewRepositorySupabase.create_or_update(review_dict)
                        stats["reviews"] += 1
                        print(f"      ✅ Сохранена рецензия от {review_dict['author_name']}")
                    except Exception as e:
                        print(f"   ⚠️  Ошибка при сохранении рецензии: {e}")
                        import traceback
                        traceback.print_exc()
        else:
            # Обновляем только лайки для существующих записей
            existing_reviews = ReviewRepositorySupabase.get_by_book_id(book_id)
            comments = api.get_work_comments(work_id)
            reviews = api.get_work_reviews(work_id)
            
            # Создаем маппинг ID -> лайки
            likes_map = {}
            for item in comments + reviews:
                item_id = str(item.get("id", item.get("commentId", item.get("reviewId", ""))))
                likes = int(item.get("likes_count", item.get("likes", 0)) or 0)
                if item_id:
                    likes_map[item_id] = likes
            
            # Обновляем лайки
            for review in existing_reviews:
                review_id = review.get("litres_review_id")
                if review_id and review_id in likes_map:
                    new_likes = likes_map[review_id]
                    if review.get("likes_count", 0) != new_likes:
                        try:
                            ReviewRepositorySupabase.update(review.get("id"), {"likes_count": new_likes})
                            stats["likes_updated"] += 1
                        except Exception as e:
                            print(f"   ⚠️  Ошибка при обновлении лайков: {e}")
        
        return stats
    
    if book_id:
        # Обновляем отзывы для одной книги
        book_data = BookRepositorySupabase.get_by_id(book_id)
        if not book_data:
            return {"success": False, "error": "Книга не найдена"}
        
        stats = process_book(book_data)
        
        return {
            "success": True,
            "book_id": book_id,
            **stats
        }
    else:
        # Обновляем отзывы для всех книг
        books_data = BookRepositorySupabase.get_all()
        total_stats = {
            "total_books": len(books_data),
            "updated_books": 0,
            "total_comments": 0,
            "total_reviews": 0,
            "total_likes_updated": 0
        }
        
        print(f"📚 Начинаем обновление для {total_stats['total_books']} книг")
        
        for idx, book_data in enumerate(books_data, 1):
            print(f"\n[{idx}/{total_stats['total_books']}] ", end="")
            stats = process_book(book_data)
            
            if stats.get("comments", 0) > 0 or stats.get("reviews", 0) > 0 or stats.get("likes_updated", 0) > 0:
                total_stats["updated_books"] += 1
            
            total_stats["total_comments"] += stats.get("comments", 0)
            total_stats["total_reviews"] += stats.get("reviews", 0)
            total_stats["total_likes_updated"] += stats.get("likes_updated", 0)
            
            # Задержка между запросами
            time.sleep(1.1)
        
        print(f"\n✅ Обновление завершено")
        return {
            "success": True,
            **total_stats
        }

