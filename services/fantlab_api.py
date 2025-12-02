"""Интеграция с FantLab.ru для получения оценок, отзывов и аннотаций через официальный API."""
import sys
from pathlib import Path
import requests
import time
import json
import re
from typing import List, Dict, Optional, Union
from datetime import datetime
from bs4 import BeautifulSoup

# Добавляем корневую папку проекта в sys.path для корректного импорта
# Это нужно, если файл запускается напрямую или импортируется из скриптов
try:
    from utils.config import Config
except ImportError:
    # Если импорт не удался, добавляем корневую папку в sys.path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from utils.config import Config


class FantLab:
    """Класс для работы с FantLab.ru API."""
    
    def __init__(self):
        self.api_url = Config.FANTLAB_API_URL or "https://api.fantlab.ru"
        self.web_url = Config.FANTLAB_WEB_URL or "https://fantlab.ru"
        self.api_key = Config.FANTLAB_API_KEY or ""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/json",
            "Accept-Charset": "utf-8",
        }
        self.api_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Charset": "utf-8",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        if self.api_key:
            self.api_headers["Authorization"] = f"Bearer {self.api_key}"
    
    def _safe_int(self, value: Union[str, int, float, None], default: int = 0) -> int:
        """
        Безопасное преобразование значения в int.
        API может возвращать строки вместо чисел (например, "work_id":"1").
        
        Args:
            value: Значение для преобразования
            default: Значение по умолчанию при ошибке
        
        Returns:
            int значение
        """
        if value is None:
            return default
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        return default
    
    def _safe_float(self, value: Union[str, int, float, None], default: float = 0.0) -> float:
        """
        Безопасное преобразование значения в float.
        API может возвращать строки вместо чисел (например, "rating":"8.91").
        
        Args:
            value: Значение для преобразования
            default: Значение по умолчанию при ошибке
        
        Returns:
            float значение
        """
        if value is None:
            return default
        if isinstance(value, float):
            return value
        if isinstance(value, int):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        return default
    
    def _clean_html_tags(self, text: str) -> str:
        """
        Очистить HTML-теги и BB-теги из текста.
        API может возвращать HTML-теги (<a href="/work320">) и BB-теги ([user]).
        
        Args:
            text: Текст с тегами
        
        Returns:
            Очищенный текст
        """
        if not text:
            return ""
        
        # Удаляем HTML-теги
        text = re.sub(r'<[^>]+>', '', text)
        
        # Удаляем BB-теги вида [user], [work] и т.п.
        text = re.sub(r'\[[^\]]+\]', '', text)
        
        # Очищаем множественные пробелы
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _get_page_html(self, url: str) -> Optional[str]:
        """
        Получить HTML страницы (используется только как fallback при недоступности API).
        
        Args:
            url: URL страницы
        
        Returns:
            HTML содержимое или None
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                response.encoding = 'utf-8'
                return response.text
            return None
        except Exception as e:
            print(f"   ❌ Ошибка получения HTML: {e}")
            return None
    
    def _extract_json_from_html(self, html: str) -> Optional[Dict]:
        """
        Извлечь JSON данные из HTML страницы (используется только как fallback).
        Ищет JSON в тегах <script> с различными паттернами.
        
        Args:
            html: HTML содержимое страницы
        
        Returns:
            Извлеченные JSON данные или None
        """
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Расширенные паттерны для поиска JSON в script тегах
        patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
            r'window\.__DATA__\s*=\s*({.+?});',
            r'window\.workData\s*=\s*({.+?});',
            r'var\s+workData\s*=\s*({.+?});',
            r'var\s+data\s*=\s*({.+?});',
            r'const\s+workData\s*=\s*({.+?});',
            r'let\s+workData\s*=\s*({.+?});',
            r'<script[^>]*type=["\']application/json["\'][^>]*>(.+?)</script>',
            r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.+?)</script>',  # Next.js
        ]
        
        # Ищем в script тегах
        script_tags = soup.find_all('script')
        for script in script_tags:
            script_text = script.string or ""
            
            # Пробуем найти JSON по паттернам
            for pattern in patterns:
                match = re.search(pattern, script_text, re.DOTALL)
                if match:
                    try:
                        json_str = match.group(1)
                        json_str = json_str.strip()
                        # Убираем возможные комментарии JavaScript
                        json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
                        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
                        return json.loads(json_str)
                    except (json.JSONDecodeError, IndexError):
                        continue
            
            # Пробуем распарсить весь script как JSON
            script_text = script_text.strip()
            if script_text.startswith('{') or script_text.startswith('['):
                try:
                    # Убираем комментарии
                    script_text = re.sub(r'//.*?$', '', script_text, flags=re.MULTILINE)
                    script_text = re.sub(r'/\*.*?\*/', '', script_text, flags=re.DOTALL)
                    return json.loads(script_text)
                except json.JSONDecodeError:
                    continue
        
        # Ищем data-атрибуты с JSON
        data_elements = soup.find_all(attrs={'data-json': True})
        for elem in data_elements:
            try:
                json_str = elem.get('data-json')
                if json_str:
                    return json.loads(json_str)
            except json.JSONDecodeError:
                continue
        
        return None
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Выполнить запрос к API FantLab.
        
        Args:
            endpoint: Эндпоинт API (например, "/work/123")
            params: Параметры запроса
        
        Returns:
            JSON ответ или None при ошибке
        """
        try:
            url = f"{self.api_url}{endpoint}"
            # Убеждаемся, что заголовки правильно закодированы
            safe_headers = {}
            for key, value in self.api_headers.items():
                if isinstance(value, str):
                    # Убираем любые не-ASCII символы из заголовков
                    safe_headers[key] = value.encode('ascii', 'ignore').decode('ascii')
                else:
                    safe_headers[key] = value
            
            response = requests.get(url, headers=safe_headers, params=params, timeout=15)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError:
                    # Если ответ не JSON, пробуем парсить как HTML или возвращаем текст
                    print(f"   ⚠️  Ответ не в формате JSON для {endpoint}")
                    return None
            elif response.status_code == 404:
                print(f"   ⚠️  Ресурс не найден: {endpoint} (404)")
                return None
            else:
                error_text = response.text[:200] if response.text else "Нет текста ответа"
                print(f"   ⚠️  Ошибка API {response.status_code} для {endpoint}: {error_text}")
                return None
        except requests.exceptions.Timeout:
            print(f"   ❌ Таймаут при запросе к {endpoint}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Ошибка подключения к FantLab API: {endpoint}")
            return None
        except Exception as e:
            print(f"   ❌ Ошибка запроса к FantLab API {endpoint}: {e}")
            return None
    
    def get_work_info(self, work_id: int) -> Dict:
        """
        Получить информацию о произведении через официальный API.
        
        Args:
            work_id: ID произведения на FantLab
        
        Returns:
            Словарь с информацией: annotation, rating, reviews_count, title, author, etc.
        """
        # Используем официальный API
        data = self._make_request(f"/work/{work_id}")
        
        # Если API не доступен, пробуем HTML как fallback
        if not data:
            url = f"{self.web_url}/work{work_id}"
            html = self._get_page_html(url)
            if html:
                data = self._extract_json_from_html(html)
        
        if not data:
            return {"error": "Не удалось получить данные"}
        
        # Извлекаем информацию согласно структуре API
        result = {
            "annotation": "",
            "rating": 0.0,
            "reviews_count": 0,
            "title": "",
            "author": ""
        }
        
        # Название произведения (work_name согласно документации)
        result["title"] = data.get("work_name") or data.get("title") or ""
        
        # Автор (authors[0].name согласно документации)
        authors = data.get("authors", [])
        if isinstance(authors, list) and len(authors) > 0:
            author_data = authors[0]
            if isinstance(author_data, dict):
                result["author"] = author_data.get("name", "")
            else:
                result["author"] = str(author_data)
        elif isinstance(authors, str):
            result["author"] = authors
        
        # Рейтинг (rating.rating согласно документации, может быть строкой)
        rating_obj = data.get("rating")
        if isinstance(rating_obj, dict):
            result["rating"] = self._safe_float(rating_obj.get("rating"), 0.0)
        else:
            result["rating"] = self._safe_float(data.get("val_midmark_by_weight"), 0.0)
        
        # Количество оценок (rating.voters согласно документации)
        if isinstance(rating_obj, dict):
            result["voters_count"] = self._safe_int(rating_obj.get("voters"), 0)
        else:
            result["voters_count"] = self._safe_int(data.get("val_voters"), 0)
        
        # Количество отзывов (val_responsecount согласно документации)
        result["reviews_count"] = self._safe_int(data.get("val_responsecount"), 0)
        
        # Аннотация (work_description согласно документации)
        annotation = data.get("work_description") or ""
        result["annotation"] = self._clean_html_tags(annotation)
        
        return result
    
    def get_work_info_extended(self, work_id: int) -> Dict:
        """
        Получить расширенную информацию о произведении через официальный API.
        
        Args:
            work_id: ID произведения на FantLab
        
        Returns:
            Словарь с расширенной информацией: awards, editions_info, translations, 
            classificatory, children, parents, films, и все поля из get_work_info()
        """
        # Используем расширенный эндпоинт API
        data = self._make_request(f"/work/{work_id}/extended")
        
        if not data:
            # Если расширенная информация недоступна, возвращаем базовую
            return self.get_work_info(work_id)
        
        # Получаем базовую информацию
        result = self.get_work_info(work_id)
        
        # Добавляем расширенную информацию
        result["awards"] = data.get("awards")
        result["editions_info"] = data.get("editions_info")
        result["editions_blocks"] = data.get("editions_blocks")
        result["translations"] = data.get("translations")
        result["classificatory"] = data.get("classificatory")
        result["children"] = data.get("children")
        result["parents"] = data.get("parents")
        result["films"] = data.get("films")
        result["work_root_saga"] = data.get("work_root_saga")
        result["la_resume"] = data.get("la_resume")
        
        return result
    
    def get_work_rating(self, work_id: int) -> float:
        """
        Получить среднюю оценку произведения.
        
        Args:
            work_id: ID произведения на FantLab
        
        Returns:
            Средняя оценка (0.0 - 10.0) или 0.0 при ошибке
        """
        data = self._make_request(f"/work/{work_id}")
        
        if not data:
            return 0.0
        
        # Используем rating.rating согласно документации
        rating_obj = data.get("rating")
        if isinstance(rating_obj, dict):
            return self._safe_float(rating_obj.get("rating"), 0.0)
        
        # Fallback на val_midmark_by_weight
        return self._safe_float(data.get("val_midmark_by_weight"), 0.0)
    
    def get_work_reviews(self, work_id: int, page: int = 1, limit: int = 100) -> List[Dict]:
        """
        Получить отзывы на произведение.
        Сначала пробует извлечь JSON из HTML, затем парсит структуру HTML.
        
        Args:
            work_id: ID произведения на FantLab
            page: Номер страницы
            limit: Количество отзывов
        
        Returns:
            Список отзывов: id, author_name, text, date, rating, likes_count
        """
        reviews = []
        
        # Получаем HTML страницу
        url = f"{self.web_url}/work{work_id}"
        html = self._get_page_html(url)
        
        if not html:
            return reviews
        
        # Стратегия 1: Пробуем извлечь JSON из HTML (отзывы могут быть встроены)
        json_data = self._extract_json_from_html(html)
        if json_data:
            # Ищем отзывы в извлеченном JSON
            reviews_data = (
                json_data.get("reviews") or 
                json_data.get("responses") or 
                json_data.get("comments") or
                json_data.get("work", {}).get("reviews") or
                json_data.get("work", {}).get("responses") or
                json_data.get("data", {}).get("reviews") or
                []
            )
            
            if isinstance(reviews_data, list) and reviews_data:
                # Обрабатываем отзывы из JSON
                for item in reviews_data[:limit]:
                    try:
                        review = self._parse_review_from_json(item, work_id)
                        if review:
                            reviews.append(review)
                    except Exception:
                        continue
                
                if reviews:
                    return reviews
            elif isinstance(reviews_data, dict):
                # Если reviews_data - словарь, пробуем извлечь список
                items = (
                    reviews_data.get("items") or 
                    reviews_data.get("list") or 
                    reviews_data.get("data") or
                    []
                )
                if isinstance(items, list) and items:
                    for item in items[:limit]:
                        try:
                            review = self._parse_review_from_json(item, work_id)
                            if review:
                                reviews.append(review)
                        except Exception:
                            continue
                    if reviews:
                        return reviews
        
        # Стратегия 2: Если JSON не найден или отзывов нет, парсим HTML структуру
        return self._parse_reviews_from_html(html, work_id, limit)
    
    def _parse_reviews_from_html(self, html: str, work_id: int, limit: int = 100) -> List[Dict]:
        """
        Парсинг отзывов из HTML страницы.
        
        Args:
            html: HTML содержимое страницы
            work_id: ID произведения
            limit: Максимальное количество отзывов
        
        Returns:
            Список отзывов
        """
        reviews = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Стратегия 1: Ищем все ссылки на пользователей (авторы отзывов)
            # Это самый надежный способ найти отзывы
            user_links = soup.find_all('a', href=re.compile(r'/user/\d+'))
            
            # Для каждой ссылки на пользователя ищем связанный блок отзыва
            processed_elements = set()
            for link in user_links:
                # Пробуем найти родительский блок отзыва на разных уровнях
                # Сначала ищем ближайший родитель с достаточным количеством текста
                current = link.parent
                best_parent = None
                max_text_length = 0
                
                # Поднимаемся по дереву до 5 уровней
                for level in range(5):
                    if current is None:
                        break
                    text = current.get_text(separator=' ', strip=True)
                    if len(text) > max_text_length and len(text) > 30:
                        # Проверяем, что это не навигация
                        classes = ' '.join(current.get('class', [])).lower()
                        elem_id = str(current.get('id', '')).lower()
                        if not any(nav in classes or nav in elem_id 
                                  for nav in ['nav', 'menu', 'header', 'footer', 'sidebar', 'breadcrumb']):
                            best_parent = current
                            max_text_length = len(text)
                    current = current.parent
                
                if best_parent and id(best_parent) not in processed_elements:
                    processed_elements.add(id(best_parent))
                    try:
                        review = self._extract_review_from_element(best_parent, work_id)
                        if review:
                            # Проверяем, что это не дубликат
                            is_duplicate = any(
                                r.get('author_name') == review.get('author_name') and 
                                r.get('text', '')[:50] == review.get('text', '')[:50]
                                for r in reviews
                            )
                            if not is_duplicate:
                                reviews.append(review)
                    except Exception:
                        continue
            
            # Стратегия 2: Если не нашли через ссылки, ищем по структуре страницы
            if not reviews:
                # Ищем секцию с отзывами по заголовку
                reviews_header = soup.find(string=re.compile(r'Отзывы читателей|Рецензии|Комментарии|Responses', re.I))
                if reviews_header:
                    container = reviews_header.find_parent(['div', 'section', 'article', 'main'])
                    if container:
                        # Ищем все блоки внутри контейнера
                        potential_reviews = container.find_all(['div', 'article', 'li'], recursive=True)
                        for elem in potential_reviews:
                            text = elem.get_text(strip=True)
                            if len(text) > 50 and elem.find('a', href=re.compile(r'/user')):
                                try:
                                    review = self._extract_review_from_element(elem, work_id)
                                    if review:
                                        reviews.append(review)
                                except Exception:
                                    continue
            
            # Ограничиваем количество
            reviews = reviews[:limit]
            
        except Exception as e:
            print(f"   ⚠️  Ошибка парсинга отзывов из HTML: {e}")
            import traceback
            traceback.print_exc()
        
        return reviews
    
    def _parse_review_from_json(self, item: Dict, work_id: int) -> Optional[Dict]:
        """
        Парсинг отзыва из JSON данных.
        
        Args:
            item: Элемент отзыва из JSON
            work_id: ID произведения
        
        Returns:
            Словарь с данными отзыва или None
        """
        try:
            # Извлекаем ID отзыва (может быть строкой)
            review_id = str(item.get("id") or item.get("review_id") or item.get("response_id") or item.get("comment_id") or f"{work_id}_{abs(hash(str(item)))}")
            
            # Извлекаем автора
            author_data = item.get("author") or item.get("user") or item.get("user_name") or {}
            if isinstance(author_data, dict):
                author_name = (
                    author_data.get("name") or 
                    author_data.get("username") or 
                    author_data.get("login") or 
                    "Анонимный читатель"
                )
            elif isinstance(author_data, str):
                author_name = author_data
            else:
                author_name = "Анонимный читатель"
            
            # Извлекаем текст отзыва
            text = (
                item.get("text") or 
                item.get("content") or 
                item.get("review_text") or 
                item.get("response_text") or 
                item.get("message") or 
                ""
            )
            text = self._clean_html_tags(str(text))
            
            if not text or len(text.strip()) < 20:
                return None
            
            # Извлекаем дату
            date_str = (
                item.get("date") or 
                item.get("created_at") or 
                item.get("created") or 
                item.get("published_at") or 
                None
            )
            
            # Извлекаем оценку (может быть строкой)
            rating = self._safe_float(item.get("rating") or item.get("score") or item.get("mark"), 0.0)
            
            # Извлекаем количество лайков (может быть строкой)
            likes_count = self._safe_int(
                item.get("likes") or 
                item.get("likes_count") or 
                item.get("plus_count") or 
                item.get("votes") or
                0
            )
            
            return {
                "id": review_id,
                "author_name": str(author_name),
                "text": text.strip(),
                "date": str(date_str) if date_str else None,
                "rating": rating,
                "likes_count": likes_count
            }
        except Exception as e:
            return None
    
    def _extract_review_from_element(self, element, work_id: int) -> Optional[Dict]:
        """
        Извлечь данные отзыва из HTML элемента.
        
        Args:
            element: BeautifulSoup элемент с отзывом
            work_id: ID произведения
        
        Returns:
            Словарь с данными отзыва или None
        """
        try:
            # Извлекаем автора (обычно ссылка на пользователя)
            author_link = element.find('a', href=re.compile(r'/user/\d+'))
            author_name = "Анонимный читатель"
            
            if author_link:
                author_name = author_link.get_text(strip=True)
                # Если имя пустое, пробуем из title или извлекаем из href
                if not author_name:
                    author_name = author_link.get('title', '')
                    if not author_name:
                        # Пробуем найти имя в соседних элементах
                        parent = author_link.find_parent()
                        if parent:
                            # Ищем текст рядом со ссылкой
                            for sibling in parent.find_all(['span', 'div', 'p']):
                                text = sibling.get_text(strip=True)
                                if text and len(text) < 50:  # Имя обычно короткое
                                    author_name = text
                                    break
            
            # Получаем весь текст элемента
            element_text = element.get_text(separator=' ', strip=True)
            
            # Извлекаем текст отзыва
            text = element_text
            
            # Убираем автора из начала текста
            if author_name and author_name != "Анонимный читатель":
                # Убираем имя автора и возможные служебные слова
                text = re.sub(rf'^{re.escape(author_name)}', '', text, count=1, flags=re.IGNORECASE)
                text = re.sub(r'^(написал|пишет|сказал|отметил)[:\s]*', '', text, flags=re.IGNORECASE)
            
            # Убираем дату (разные форматы)
            date_patterns = [
                r'\d{1,2}\s+\w+\s+\d{4}',  # "15 января 2024"
                r'\d{4}-\d{2}-\d{2}',      # "2024-01-15"
                r'\d{2}\.\d{2}\.\d{4}',   # "15.01.2024"
            ]
            for pattern in date_patterns:
                text = re.sub(pattern, '', text, count=1)
            
            # Убираем служебные фразы и теги
            text = re.sub(r'Оценка[:\s]*\d+', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\[.*?\]', '', text)  # BB-теги
            text = self._clean_html_tags(text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Проверяем, что текст достаточно длинный и не является служебным
            if not text or len(text) < 20:
                return None
            
            # Исключаем служебные тексты
            if any(skip in text.lower() for skip in ['читать далее', 'читать полностью', 'развернуть', 'свернуть']):
                return None
            
            # Извлекаем дату
            date_str = None
            for pattern in date_patterns:
                date_match = re.search(pattern, element_text)
                if date_match:
                    date_str = date_match.group(0)
                    break
            
            # Извлекаем оценку
            rating = 0.0
            rating_match = re.search(r'Оценка[:\s]+(\d+)', element_text, re.I)
            if rating_match:
                rating = self._safe_float(rating_match.group(1), 0.0)
            else:
                # Пробуем найти число от 1 до 10 в контексте оценки
                rating_match = re.search(r'(?:оценка|rating|mark|оценил)[:\s]*(\d+)', element_text, re.I)
                if rating_match:
                    rating_value = self._safe_float(rating_match.group(1), 0.0)
                    if 1 <= rating_value <= 10:
                        rating = rating_value
            
            # Извлекаем количество лайков/плюсов
            likes_count = 0
            # Ищем паттерны типа "+5", "-2", "5 плюсов", "[+5]", "[-2]" и т.п.
            likes_patterns = [
                r'\[?\s*(\+|\-)\s*(\d+)\s*\]?',  # [+5], [-2]
                r'(\d+)\s*(?:плюс|лайк|like|голос)',  # "5 плюсов"
                r'(?:плюс|лайк|like)[:\s]*(\d+)',  # "плюс: 5"
            ]
            for pattern in likes_patterns:
                likes_match = re.search(pattern, element_text, re.I)
                if likes_match:
                    likes_count = self._safe_int(likes_match.group(2) or likes_match.group(1), 0)
                    break
            
            # Генерируем уникальный ID отзыва
            review_id = f"{work_id}_{abs(hash(author_name + str(date_str) + text[:50]))}"
            
            return {
                "id": str(review_id),
                "author_name": author_name,
                "text": text,
                "date": date_str,
                "rating": rating,
                "likes_count": likes_count
            }
        except Exception as e:
            return None
        
        # Обрабатываем разные форматы ответа
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Может быть вложенная структура
            items = (
                data.get("reviews") or 
                data.get("comments") or 
                data.get("items") or 
                data.get("data") or 
                data.get("list") or
                data.get("work", {}).get("reviews", []) or
                []
            )
            # Если это пагинация
            if not items and "results" in data:
                items = data.get("results", [])
        
        # Обрабатываем каждый отзыв
        for item in items:
            try:
                # Извлекаем ID отзыва (может быть строкой согласно документации)
                review_id = str(item.get("id") or item.get("review_id") or item.get("comment_id") or f"{work_id}_{len(reviews)}")
                
                # Извлекаем автора
                author_data = item.get("author") or item.get("user") or item.get("user_name") or {}
                if isinstance(author_data, dict):
                    author_name = (
                        author_data.get("name") or 
                        author_data.get("username") or 
                        author_data.get("login") or 
                        "Анонимный читатель"
                    )
                elif isinstance(author_data, str):
                    author_name = author_data
                else:
                    author_name = "Анонимный читатель"
                
                # Извлекаем текст отзыва
                text = (
                    item.get("text") or 
                    item.get("content") or 
                    item.get("review_text") or 
                    item.get("comment_text") or 
                    item.get("message") or 
                    ""
                )
                
                # Извлекаем дату
                date_str = (
                    item.get("date") or 
                    item.get("created_at") or 
                    item.get("created") or 
                    item.get("published_at") or 
                    None
                )
                
                # Извлекаем оценку (может быть строкой)
                rating = self._safe_float(item.get("rating") or item.get("score") or item.get("mark"), 0.0)
                
                # Извлекаем количество лайков (может быть строкой)
                likes_count = self._safe_int(
                    item.get("likes") or 
                    item.get("likes_count") or 
                    item.get("plus_count") or 
                    item.get("votes") or
                    (item.get("likes", {}) if isinstance(item.get("likes"), dict) else {}).get("count") if isinstance(item.get("likes"), dict) else None,
                    0
                )
                
                # Очищаем текст от HTML и BB-тегов
                text_cleaned = self._clean_html_tags(str(text))
                
                # Добавляем отзыв, если есть текст
                if text_cleaned and len(text_cleaned.strip()) > 10:
                    review = {
                        "id": str(review_id),
                        "author_name": str(author_name),
                        "text": text_cleaned.strip(),
                        "date": str(date_str) if date_str else None,
                        "rating": rating,
                        "likes_count": likes_count
                    }
                    reviews.append(review)
            except Exception as e:
                print(f"   ⚠️  Ошибка обработки отзыва: {e}")
                continue
        
        return reviews
    
    def get_series_info(self, series_id: int) -> Dict:
        """
        Получить информацию о цикле/серии через официальный API.
        Циклы тоже являются work на FantLab, поэтому используем /work/{series_id}.
        
        Args:
            series_id: ID цикла на FantLab
        
        Returns:
            Словарь с информацией: annotation, rating, reviews_count, works, title
        """
        # Циклы тоже являются work на FantLab, используем тот же эндпоинт
        data = self._make_request(f"/work/{series_id}")
        
        # Если API не доступен, пробуем HTML как fallback
        if not data:
            url = f"{self.web_url}/work{series_id}"
            html = self._get_page_html(url)
            if html:
                data = self._extract_json_from_html(html)
        
        if not data:
            return {"error": "Не удалось получить данные"}
        
        # Используем те же поля, что и для произведения
        result = {
            "annotation": "",
            "rating": 0.0,
            "reviews_count": 0,
            "title": "",
            "works": []
        }
        
        # Название (work_name согласно документации)
        result["title"] = data.get("work_name") or data.get("title") or ""
        
        # Рейтинг (rating.rating согласно документации)
        rating_obj = data.get("rating")
        if isinstance(rating_obj, dict):
            result["rating"] = self._safe_float(rating_obj.get("rating"), 0.0)
        else:
            result["rating"] = self._safe_float(data.get("val_midmark_by_weight"), 0.0)
        
        # Количество отзывов (val_responsecount согласно документации)
        result["reviews_count"] = self._safe_int(data.get("val_responsecount"), 0)
        
        # Аннотация (work_description согласно документации)
        annotation = data.get("work_description") or ""
        result["annotation"] = self._clean_html_tags(annotation)
        
        # Произведения в цикле (children из extended или из базовой информации)
        # Пробуем получить extended для получения children
        extended_data = self._make_request(f"/work/{series_id}/extended")
        if extended_data and extended_data.get("children"):
            result["works"] = extended_data.get("children", [])
        else:
            # Fallback на другие возможные поля
            works = data.get("works") or data.get("children") or []
            result["works"] = works if isinstance(works, list) else []
        
        return result
    
    def get_series_rating(self, series_id: int) -> float:
        """
        Получить среднюю оценку цикла.
        Циклы тоже являются work на FantLab.
        
        Args:
            series_id: ID цикла на FantLab
        
        Returns:
            Средняя оценка (0.0 - 10.0) или 0.0 при ошибке
        """
        # Используем тот же метод, что и для произведения
        return self.get_work_rating(series_id)
    
    def get_series_reviews(self, series_id: int, page: int = 1, limit: int = 100) -> List[Dict]:
        """
        Получить отзывы на цикл.
        Циклы тоже являются work на FantLab, используем тот же метод.
        
        Args:
            series_id: ID цикла на FantLab
            page: Номер страницы
            limit: Количество отзывов
        
        Returns:
            Список отзывов: id, author_name, text, date, rating, likes_count
        """
        return self.get_work_reviews(series_id, page=page, limit=limit)


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Парсинг даты из различных форматов."""
    if not date_str:
        return None
    
    try:
        if "T" in str(date_str):
            return datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        # Другие форматы можно добавить при необходимости
    except:
        pass
    
    return None


def sync_reviews_from_fantlab(book_id: Optional[int] = None, update_ratings_only: bool = False) -> Dict:
    """
    Синхронизировать отзывы и оценки с FantLab.
    
    Args:
        book_id: ID книги (если None, обновляются все книги)
        update_ratings_only: Если True, обновляются только оценки существующих записей
    
    Returns:
        Словарь со статистикой обновления
    """
    import streamlit as st
    
    from database.repository_supabase import BookRepositorySupabase, ReviewRepositorySupabase
    
    api = FantLab()
    
    # Логирование для отладки
    try:
        st.write(f"🔍 Начало синхронизации с FantLab (book_id={book_id})")
    except:
        print(f"🔍 Начало синхронизации с FantLab (book_id={book_id})")
    
    def process_book(book_data: Dict) -> Dict:
        """Обработать одну книгу."""
        book_id = book_data.get("id")
        book_title = book_data.get("title", "")
        work_id = book_data.get("fantlab_work_id")
        series_id = book_data.get("fantlab_series_id")
        
        stats = {
            "book_id": book_id,
            "reviews": 0,
            "rating": 0.0,
            "error": None
        }
        
        if not work_id:
            stats["error"] = "fantlab_work_id не установлен"
            return stats
        
        print(f"📖 Обработка: '{book_title}' (work_id: {work_id})")
        
        try:
            # Получаем информацию о произведении
            work_info = api.get_work_info(work_id)
            
            if "error" not in work_info:
                stats["rating"] = work_info.get("rating", 0.0)
            
            if not update_ratings_only:
                # Получаем отзывы на произведение
                reviews = api.get_work_reviews(work_id)
                print(f"   📄 Найдено отзывов: {len(reviews)}")
                
                for review_data in reviews:
                    review_dict = {
                        "book_id": book_id,
                        "litres_review_id": str(review_data.get("id", "")),
                        "comment_type": "review",
                        "author_name": review_data.get("author_name", "Анонимный читатель"),
                        "text": review_data.get("text", ""),
                        "likes_count": int(review_data.get("likes_count", 0)),
                        "date": _parse_date(review_data.get("date"))
                    }
                    
                    if review_dict["text"] and len(review_dict["text"].strip()) > 0:
                        try:
                            ReviewRepositorySupabase.create_or_update(review_dict)
                            stats["reviews"] += 1
                        except Exception as e:
                            print(f"   ⚠️  Ошибка при сохранении отзыва: {e}")
            
            time.sleep(0.5)  # Задержка между запросами
            
        except Exception as e:
            stats["error"] = str(e)
            print(f"   ❌ Ошибка обработки книги: {e}")
        
        return stats
    
    def process_series(series_id: int) -> Dict:
        """Обработать цикл (получить отзывы на цикл)."""
        stats = {
            "series_id": series_id,
            "reviews": 0,
            "rating": 0.0
        }
        
        try:
            series_info = api.get_series_info(series_id)
            
            if "error" not in series_info:
                stats["rating"] = series_info.get("rating", 0.0)
            
            if not update_ratings_only:
                reviews = api.get_series_reviews(series_id)
                print(f"📚 Отзывов на цикл: {len(reviews)}")
                
                # Сохраняем отзывы на цикл
                # Для простоты сохраняем их с book_id первой книги цикла
                books_data = BookRepositorySupabase.get_all()
                first_book_id = books_data[0].get("id") if books_data else None
                
                for review_data in reviews:
                    review_dict = {
                        "book_id": first_book_id,  # Привязываем к первой книге
                        "litres_review_id": f"series_{series_id}_{review_data.get('id', '')}",
                        "comment_type": "review",
                        "author_name": review_data.get("author_name", "Анонимный читатель"),
                        "text": review_data.get("text", ""),
                        "likes_count": int(review_data.get("likes_count", 0)),
                        "date": _parse_date(review_data.get("date"))
                    }
                    
                    if review_dict["text"] and len(review_dict["text"].strip()) > 0:
                        try:
                            ReviewRepositorySupabase.create_or_update(review_dict)
                            stats["reviews"] += 1
                        except Exception as e:
                            print(f"   ⚠️  Ошибка при сохранении отзыва на цикл: {e}")
            
        except Exception as e:
            print(f"❌ Ошибка обработки цикла: {e}")
        
        return stats
    
    if book_id:
        book_data = BookRepositorySupabase.get_by_id(book_id)
        if not book_data:
            error_msg = {"success": False, "error": "Книга не найдена"}
            try:
                st.error("❌ Книга не найдена")
            except:
                pass
            return error_msg
        
        stats = process_book(book_data)
        result = {"success": True, "book_id": book_id, **stats}
        
        if stats.get("error"):
            result["success"] = False
            result["error"] = stats["error"]
        
        try:
            if result.get("success"):
                st.success(f"✅ Обновлено: {stats.get('reviews', 0)} отзывов, оценка: {stats.get('rating', 0):.2f}")
            else:
                st.error(f"❌ Ошибка: {result.get('error', 'Неизвестная ошибка')}")
        except:
            pass
        
        return result
    else:
        books_data = BookRepositorySupabase.get_all()
        total_stats = {
            "total_books": len(books_data),
            "updated_books": 0,
            "total_reviews": 0,
            "total_rating": 0.0
        }
        
        # Обрабатываем цикл (если есть series_id у первой книги)
        if books_data:
            first_book = books_data[0]
            series_id = first_book.get("fantlab_series_id")
            if series_id:
                series_stats = process_series(series_id)
                total_stats["series_rating"] = series_stats.get("rating", 0.0)
                total_stats["series_reviews"] = series_stats.get("reviews", 0)
        
        for book_data in books_data:
            stats = process_book(book_data)
            
            if stats.get("reviews", 0) > 0 or stats.get("rating", 0) > 0:
                total_stats["updated_books"] += 1
            
            total_stats["total_reviews"] += stats.get("reviews", 0)
            total_stats["total_rating"] += stats.get("rating", 0.0)
            
            time.sleep(1)
        
        return {"success": True, **total_stats}

