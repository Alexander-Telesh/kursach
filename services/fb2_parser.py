"""Парсер FB2 файлов для чтения и отображения."""
import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from utils.config import Config


class FB2Parser:
    """Класс для парсинга FB2 файлов."""
    
    # Namespace для FB2
    FB2_NAMESPACE = {
        'fb2': 'http://www.gribuser.ru/xml/fictionbook/2.0',
        'l': 'http://www.w3.org/1999/xlink'
    }
    
    @staticmethod
    def parse_fb2(file_path: str) -> Dict:
        """
        Парсить FB2 файл и извлечь метаданные и содержимое.
        
        Returns:
            Словарь с ключами: title, author, description, sections, cover
        """
        if not os.path.exists(file_path):
            return {"error": "Файл не найден"}
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Извлекаем метаданные
            title_info = root.find('.//fb2:title-info', FB2Parser.FB2_NAMESPACE)
            
            title = ""
            if title_info is not None:
                title_elem = title_info.find('fb2:book-title', FB2Parser.FB2_NAMESPACE)
                if title_elem is not None:
                    title = title_elem.text or ""
            
            author = ""
            if title_info is not None:
                author_elem = title_info.find('fb2:author/fb2:first-name', FB2Parser.FB2_NAMESPACE)
                if author_elem is not None:
                    author = author_elem.text or ""
                last_name_elem = title_info.find('fb2:author/fb2:last-name', FB2Parser.FB2_NAMESPACE)
                if last_name_elem is not None:
                    author += " " + (last_name_elem.text or "")
                author = author.strip()
            
            description = ""
            if title_info is not None:
                annotation_elem = title_info.find('fb2:annotation', FB2Parser.FB2_NAMESPACE)
                if annotation_elem is not None:
                    description = FB2Parser._extract_text(annotation_elem)
            
            # Извлекаем секции (главы)
            body = root.find('.//fb2:body', FB2Parser.FB2_NAMESPACE)
            sections = []
            if body is not None:
                section_elems = body.findall('.//fb2:section', FB2Parser.FB2_NAMESPACE)
                for section_elem in section_elems:
                    section_title = ""
                    title_elem = section_elem.find('fb2:title', FB2Parser.FB2_NAMESPACE)
                    if title_elem is not None:
                        section_title = FB2Parser._extract_text(title_elem)
                    
                    section_text = FB2Parser._extract_text(section_elem)
                    sections.append({
                        "title": section_title,
                        "text": section_text
                    })
            
            # Извлекаем обложку
            cover = None
            if title_info is not None:
                cover_elem = title_info.find('fb2:coverpage/fb2:image', FB2Parser.FB2_NAMESPACE)
                if cover_elem is not None:
                    cover_href = cover_elem.get('{http://www.w3.org/1999/xlink}href', '')
                    if cover_href.startswith('#'):
                        cover_id = cover_href[1:]
                        binary_elem = root.find(f'.//fb2:binary[@id="{cover_id}"]', FB2Parser.FB2_NAMESPACE)
                        if binary_elem is not None:
                            cover = binary_elem.text
            
            return {
                "title": title,
                "author": author,
                "description": description,
                "sections": sections,
                "cover": cover
            }
            
        except ET.ParseError as e:
            return {"error": f"Ошибка парсинга XML: {e}"}
        except Exception as e:
            return {"error": f"Ошибка при чтении файла: {e}"}
    
    @staticmethod
    def _extract_text(element) -> str:
        """Извлечь весь текст из элемента и его дочерних элементов."""
        if element is None:
            return ""
        
        text_parts = []
        
        # Используем BeautifulSoup для более удобной обработки
        xml_str = ET.tostring(element, encoding='unicode')
        soup = BeautifulSoup(xml_str, 'xml')
        
        # Извлекаем текст, сохраняя структуру
        for tag in soup.find_all(['p', 'strong', 'emphasis', 'text-author', 'cite']):
            text_parts.append(tag.get_text(separator=' ', strip=True))
        
        if not text_parts:
            text_parts.append(soup.get_text(separator=' ', strip=True))
        
        return ' '.join(text_parts)
    
    @staticmethod
    def parse_fb2_to_html(file_path: str) -> str:
        """
        Конвертировать FB2 файл в HTML для отображения.
        
        Returns:
            HTML строка с содержимым книги
        """
        parsed = FB2Parser.parse_fb2(file_path)
        
        if "error" in parsed:
            return f"<p>Ошибка: {parsed['error']}</p>"
        
        html_parts = []
        
        # Заголовок
        if parsed.get("title"):
            html_parts.append(f"<h1>{parsed['title']}</h1>")
        
        # Автор
        if parsed.get("author"):
            html_parts.append(f"<p><strong>Автор:</strong> {parsed['author']}</p>")
        
        # Описание
        if parsed.get("description"):
            html_parts.append(f"<div class='description'>{parsed['description']}</div>")
        
        # Секции
        for section in parsed.get("sections", []):
            if section.get("title"):
                html_parts.append(f"<h2>{section['title']}</h2>")
            if section.get("text"):
                # Заменяем переносы строк на <br> и параграфы
                text = section['text'].replace('\n', '<br>')
                html_parts.append(f"<div class='section'>{text}</div>")
        
        return "\n".join(html_parts)
    
    @staticmethod
    def get_fb2_files() -> List[str]:
        """Получить список всех FB2 файлов в папке books."""
        books_dir = Config.BOOKS_DIR
        if not os.path.exists(books_dir):
            return []
        
        fb2_files = []
        for filename in os.listdir(books_dir):
            if filename.lower().endswith('.fb2'):
                fb2_files.append(os.path.join(books_dir, filename))
        
        return sorted(fb2_files)





