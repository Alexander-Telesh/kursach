import requests

BASE_URL = "https://api.fantlab.ru"

def get_work(work_id: int):
    """Получить основную информацию о произведении"""
    url = f"{BASE_URL}/work/{work_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_work_extended(work_id: int):
    """Получить расширенную информацию о произведении"""
    url = f"{BASE_URL}/work/{work_id}/extended"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_similar_works(work_id: int):
    """Получить список похожих произведений"""
    url = f"{BASE_URL}/work/{work_id}/similars"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def set_mark(id_1: int, id_2: int, mark: int, cookies: dict):
    """
    Поставить или удалить оценку произведению.
    mark = 0 → удалить оценку
    mark = 1–10 → выставить оценку
    """
    url = f"https://fantlab.ru/work{id_1}/ajaxsetmark{mark}towork{id_2}"
    response = requests.get(url, cookies=cookies)
    response.raise_for_status()
    return response.json()

def add_similar(work_id: int, analog_work_id: int, cookies: dict):
    """Добавить похожее произведение"""
    url = f"https://fantlab.ru/work{work_id}/analog{analog_work_id}/add"
    response = requests.get(url, cookies=cookies)
    response.raise_for_status()
    return response.json()

def remove_similar(work_id: int, analog_work_id: int, cookies: dict):
    """Удалить похожее произведение"""
    url = f"https://fantlab.ru/work{work_id}/analog{analog_work_id}/remove"
    response = requests.get(url, cookies=cookies)
    response.raise_for_status()
    return response.json()
