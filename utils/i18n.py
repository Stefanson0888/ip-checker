import json
import os
from typing import Dict, Optional
from fastapi import Request

# Підтримувані мови
SUPPORTED_LANGUAGES = ['en', 'de', 'pl', 'hi', 'uk', 'ru']
DEFAULT_LANGUAGE = 'en'

# Кеш для перекладів
_translations_cache: Dict[str, Dict[str, str]] = {}

def load_translations() -> Dict[str, Dict[str, str]]:
    """Завантажує всі переклади в кеш"""
    global _translations_cache
    
    if _translations_cache:
        return _translations_cache
    
    translations = {}
    
    for lang in SUPPORTED_LANGUAGES:
        file_path = f"locales/{lang}/messages.json"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                translations[lang] = json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Translation file not found: {file_path}")
            translations[lang] = {}
        except json.JSONDecodeError:
            print(f"⚠️ Invalid JSON in: {file_path}")
            translations[lang] = {}
    
    _translations_cache = translations
    return translations

def get_language_from_request(request: Request) -> str:
    """Визначає мову з URL або заголовків"""
    # 1. З URL шляху (/en/, /de/, /pl/, /hi/)
    path = request.url.path
    path_parts = path.strip('/').split('/')
    
    if path_parts and path_parts[0] in SUPPORTED_LANGUAGES:
        return path_parts[0]
    
    # 2. З Accept-Language заголовка
    accept_language = request.headers.get('accept-language', '')
    
    for lang in SUPPORTED_LANGUAGES:
        if lang in accept_language.lower():
            return lang
    
    # 3. За замовчуванням
    return DEFAULT_LANGUAGE

def get_language_from_path(path: str) -> tuple[str, str]:
    """Витягує мову з шляху та повертає (lang, clean_path)"""
    path_parts = path.strip('/').split('/')
    
    if path_parts and path_parts[0] in SUPPORTED_LANGUAGES:
        lang = path_parts[0]
        clean_path = '/' + '/'.join(path_parts[1:]) if len(path_parts) > 1 else '/'
        return lang, clean_path
    
    return DEFAULT_LANGUAGE, path

def translate(key: str, lang: str, **kwargs) -> str:
    """Перекладає ключ на вказану мову"""
    translations = load_translations()
    
    # Спробуємо знайти переклад
    text = translations.get(lang, {}).get(key)
    
    # Fallback на англійську
    if not text:
        text = translations.get(DEFAULT_LANGUAGE, {}).get(key)
    
    # Fallback на ключ
    if not text:
        text = key
    
    # Форматування (для {country} тощо)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    
    return text

class Translator:
    """Клас-помічник для перекладів в шаблонах"""
    
    def __init__(self, lang: str):
        self.lang = lang
    
    def t(self, key: str, **kwargs) -> str:
        """Скорочений метод для перекладу"""
        return translate(key, self.lang, **kwargs)
    
    def __call__(self, key: str, **kwargs) -> str:
        """Дозволяє викликати як функцію: _(key)"""
        return self.t(key, **kwargs)

def get_language_urls(current_path: str, current_lang: str) -> Dict[str, str]:
    """Генерує URL для всіх мов"""
    urls = {}
    
    # Видаляємо поточну мову з шляху
    _, clean_path = get_language_from_path(current_path)
    
    for lang in SUPPORTED_LANGUAGES:
        if lang == DEFAULT_LANGUAGE:
            # Англійська за замовчуванням без префіксу
            urls[lang] = clean_path
        else:
            # Інші мови з префіксом
            urls[lang] = f"/{lang}{clean_path}"
    
    return urls

def get_hreflang_urls(base_url: str, current_path: str) -> Dict[str, str]:
    """Генерує hreflang URL для SEO"""
    language_urls = get_language_urls(current_path, DEFAULT_LANGUAGE)
    
    hreflang_urls = {}
    for lang, path in language_urls.items():
        hreflang_urls[lang] = f"{base_url.rstrip('/')}{path}"
    
    return hreflang_urls