from dotenv import load_dotenv
import os
import httpx 
import json
from pathlib import Path

load_dotenv()
IPHUB_API_KEY = os.getenv("IPHUB_API_KEY")

# Змінна для відстеження стану IPHub API
IPHUB_ENABLED = bool(IPHUB_API_KEY)

# 🌍 ДОДАНО: Завантаження перекладів
def load_translations():
    """Завантажуємо всі переклади з папки locales"""
    translations = {}
    locales_dir = Path("locales")
    
    if not locales_dir.exists():
        print("⚠️ Папка locales не знайдена! Створіть її з файлами перекладів")
        return {"en": {}, "uk": {}, "de": {}, "hi": {}}
    
    for lang in ['en', 'de', 'uk', 'hi']:
        lang_file = locales_dir / lang / "messages.json"
        if lang_file.exists():
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    translations[lang] = json.load(f)
                print(f"✅ Завантажено переклад: {lang}")
            except Exception as e:
                print(f"❌ Помилка завантаження {lang}: {e}")
                translations[lang] = {}
        else:
            print(f"⚠️ Файл {lang_file} не знайдено")
            translations[lang] = {}
    
    return translations

# Завантажуємо переклади при старті
TRANSLATIONS = load_translations()

def get_language_from_request(request) -> str:
    """Визначаємо мову користувача з URL або заголовків"""
    # Спочатку перевіряємо URL шлях
    path = request.url.path
    if path.startswith('/de/') or path == '/de':
        return 'de'
    if path.startswith('/uk/') or path == '/uk': 
        return 'uk'
    if path.startswith('/hi/') or path == '/hi':
        return 'hi'
    if path.startswith('/en/') or path == '/en':
        return 'en'
    
    # Потім дивимось на заголовок Accept-Language
    accept_lang = request.headers.get('accept-language', '').lower()
    if 'de' in accept_lang and 'de' not in ['en', 'uk', 'hi']:
        return 'de'
    if 'uk' in accept_lang:
        return 'uk' 
    if 'hi' in accept_lang:
        return 'hi'
    
    # За замовчуванням - англійська
    return 'en'

def translate(key: str, lang: str) -> str:
    """Функція для перекладу тексту"""
    return TRANSLATIONS.get(lang, {}).get(key, key)

def get_language_info(lang: str) -> dict:
    """Повертає інформацію про мову для SEO та відображення"""
    languages = {
        'en': {
            'code': 'en',
            'name': 'English',
            'flag': '🇺🇸',
            'url': '/',
            'hreflang': 'en',
            'locale': 'en_US'
        },
        'de': {
            'code': 'de', 
            'name': 'Deutsch',
            'flag': '🇩🇪',
            'url': '/de/',
            'hreflang': 'de',
            'locale': 'de_DE'
        },
        'uk': {
            'code': 'uk',
            'name': 'Українська', 
            'flag': '🇺🇦',
            'url': '/uk/',
            'hreflang': 'uk',
            'locale': 'uk_UA'
        },
        'hi': {
            'code': 'hi',
            'name': 'हिन्दी',
            'flag': '🇮🇳', 
            'url': '/hi/',
            'hreflang': 'hi',
            'locale': 'hi_IN'
        }
    }
    return languages.get(lang, languages['en'])

async def fetch_iphub_info(ip: str) -> dict:
    global IPHUB_ENABLED  # ✅ Перенесено на початок функції
    
    # Якщо IPHub відключений, повертаємо пустий словник
    if not IPHUB_ENABLED:
        return {}
        
    url = f"https://v2.api.iphub.info/ip/{ip}"
    headers = {"X-Key": IPHUB_API_KEY}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:  # додав timeout
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                # Невалідний API ключ - відключаємо IPHub
                IPHUB_ENABLED = False
                print(f"❌ IPHub API key invalid - disabling IPHub service")
                print(f"Response: {response.text}")
                return {}
            elif response.status_code == 429:
                # Rate limit exceeded
                print(f"⚠️ IPHub rate limit exceeded: {response.text}")
                return {}
            else:
                print(f"⚠️ IPHub returned status {response.status_code}: {response.text}")
                return {}
                
    except httpx.TimeoutException:
        print(f"⏰ IPHub timeout for IP {ip}")
        return {}
    except Exception as e:
        print(f"❌ IPHub error: {e}")
        return {}

from fastapi import FastAPI, Request, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from utils.ip import get_client_ip, fetch_ip_info
from user_agents import parse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 🌍 ДОДАНО: Реєструємо функції для шаблонів
templates.env.globals['translate'] = translate
templates.env.globals['get_language_info'] = get_language_info

@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    return FileResponse("static/robots.txt", media_type="text/plain")

@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    return FileResponse("static/sitemap.xml", media_type="application/xml")

# 🌍 ЗМІНЕНО: Додано маршрути для всіх мов
@app.get("/", response_class=HTMLResponse)
@app.get("/en/", response_class=HTMLResponse)
@app.get("/de/", response_class=HTMLResponse)
@app.get("/uk/", response_class=HTMLResponse)
@app.get("/hi/", response_class=HTMLResponse)
async def get_ip(request: Request):
    client_ip = await get_client_ip(request)
    ip_data = await fetch_ip_info(client_ip) or {}
    iphub_data = await fetch_iphub_info(client_ip) or {}
    
    # Визначаємо мову
    language = get_language_from_request(request)
    
    return render_ip_template(request, ip_data, client_ip, iphub_data, language)

# 🌍 ЗМІНЕНО: Додано підтримку мов в lookup
@app.get("/lookup", response_class=HTMLResponse)
@app.get("/en/lookup", response_class=HTMLResponse)
@app.get("/de/lookup", response_class=HTMLResponse) 
@app.get("/uk/lookup", response_class=HTMLResponse)
@app.get("/hi/lookup", response_class=HTMLResponse)
async def lookup_ip(request: Request, ip: str = Query(...)):
    ip_data = await fetch_ip_info(ip) or {}
    iphub_data = await fetch_iphub_info(ip) or {}
    
    # Визначаємо мову
    language = get_language_from_request(request)
    
    return render_ip_template(request, ip_data, ip, iphub_data, language)

# 🌍 ЗМІНЕНО: Додано параметр language
def render_ip_template(request: Request, ip_data: dict, ip: str, iphub_data: dict = None, language: str = 'uk'):
    user_agent_str = request.headers.get("user-agent", "")
    user_agent = parse(user_agent_str)

    connection = ip_data.get("connection", {})
    security = ip_data.get("security", {})
    timezone = ip_data.get("timezone", {})
    currency = ip_data.get("currency", {})

    flag_url = (
        f"https://flagcdn.com/256x192/{ip_data.get('country_code', '').lower()}.png"
        if ip_data.get("country_code") else None
    )

    languages_raw = ip_data.get("languages", [])
    language_display = ", ".join(languages_raw) if isinstance(languages_raw, list) else str(languages_raw)

    # 🌍 ДОДАНО: Контекст з мовою та перекладами
    context = {
        "request": request,
        "ip": ip,
        "type": ip_data.get("type", "Unknown"),
        "isp": connection.get("isp", "Unknown"),
        "asn": connection.get("asn", "Unknown"),
        "hostname": connection.get("domain", "Unknown"),
        "is_proxy": security.get("proxy", False),
        "is_vpn": security.get("vpn", False),
        "is_tor": security.get("tor", False),
        "user_agent": user_agent_str,
        "browser": user_agent.browser.family,
        "os": user_agent.os.family,
        "city": ip_data.get("city", "Unknown"),
        "region": ip_data.get("region", "Unknown"),
        "country": ip_data.get("country", "Unknown"),
        "country_code": ip_data.get("country_code", "Unknown"),
        "postal": ip_data.get("postal", "Unknown"),
        "calling_code": ip_data.get("calling_code", "Unknown"),
        "latitude": ip_data.get("latitude"),
        "longitude": ip_data.get("longitude"),
        "timezone": timezone.get("id", "Unknown"),
        "currency": currency.get("code", "Unknown"),
        "language": language_display,
        "flag_url": flag_url,
        "iphub_block": iphub_data.get("block") if iphub_data else None,
        "iphub_isp": iphub_data.get("isp") if iphub_data else None,
        "iphub_hostname": iphub_data.get("hostname") if iphub_data else None,
        
        # 🌍 ДОДАНО: Мовні змінні
        "current_language": language,
        "language_info": get_language_info(language),
        "available_languages": ['en', 'de', 'uk', 'hi'],
        
        # 🌍 ДОДАНО: SEO мета дані
        "page_title": translate("title", language),
        "page_description": translate("description", language),
        
        # 🌍 ДОДАНО: URL для hreflang
        "hreflang_urls": {
            "en": request.url_for("get_ip").replace(request.url.path, "/"),
            "de": request.url_for("get_ip").replace(request.url.path, "/de/"), 
            "uk": request.url_for("get_ip").replace(request.url.path, "/uk/"),
            "hi": request.url_for("get_ip").replace(request.url.path, "/hi/")
        }
    }

    return templates.TemplateResponse("index.html", context)

# Додаткова функція для перевірки стану IPHub (опціонально)
@app.get("/iphub-status")
async def iphub_status():
    return {
        "enabled": IPHUB_ENABLED,
        "api_key_present": bool(IPHUB_API_KEY)
    }

# 🌍 ДОДАНО: API ендпоінт для отримання перекладів (для AJAX)
@app.get("/api/translations/{language}")
async def get_translations(language: str):
    """API для отримання перекладів"""
    if language not in ['en', 'de', 'uk', 'hi']:
        language = 'en'
    
    return {
        "language": language,
        "translations": TRANSLATIONS.get(language, {}),
        "language_info": get_language_info(language)
    }

# 🌍 ДОДАНО: Редірект для старих URL
@app.get("/index")
@app.get("/index.html") 
async def redirect_to_main(request: Request):
    """Редірект зі старих URL на головну"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=301)