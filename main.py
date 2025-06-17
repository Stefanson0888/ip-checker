from dotenv import load_dotenv
import os
import httpx
import json
from pathlib import Path
from urllib.parse import urljoin

from fastapi import FastAPI, Request, Query
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from utils.ip import get_client_ip, fetch_ip_info
from user_agents import parse

load_dotenv()
IPHUB_API_KEY = os.getenv("IPHUB_API_KEY")
IPHUB_ENABLED = bool(IPHUB_API_KEY)

# Load translations
def load_translations():
    translations = {}
    locales_dir = Path("locales")
    if not locales_dir.exists():
        print("⚠️ Папка locales не знайдена! Створіть її з файлами перекладів")
        return {lang: {} for lang in ['en', 'uk', 'de', 'hi']}

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

TRANSLATIONS = load_translations()

def get_language_from_request(request) -> str:
    path = request.url.path
    for lang in ['de', 'uk', 'hi', 'en']:
        if path.startswith(f'/{lang}/') or path == f'/{lang}':
            return lang

    accept_lang = request.headers.get('accept-language', '').lower()
    for lang in ['uk', 'de', 'hi']:
        if lang in accept_lang:
            return lang
    return 'en'

def translate(key: str, lang: str) -> str:
    return TRANSLATIONS.get(lang, {}).get(key, key)

def get_language_info(lang: str) -> dict:
    languages = {
        'en': {"code": "en", "name": "English", "flag": "🇺🇸", "url": "/", "hreflang": "en", "locale": "en_US"},
        'de': {"code": "de", "name": "Deutsch", "flag": "🇩🇪", "url": "/de/", "hreflang": "de", "locale": "de_DE"},
        'uk': {"code": "uk", "name": "Українська", "flag": "🇺🇦", "url": "/uk/", "hreflang": "uk", "locale": "uk_UA"},
        'hi': {"code": "hi", "name": "हिन्दी", "flag": "🇮🇳", "url": "/hi/", "hreflang": "hi", "locale": "hi_IN"}
    }
    return languages.get(lang, languages['en'])

async def fetch_iphub_info(ip: str) -> dict:
    global IPHUB_ENABLED
    if not IPHUB_ENABLED:
        return {}

    url = f"https://v2.api.iphub.info/ip/{ip}"
    headers = {"X-Key": IPHUB_API_KEY}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                IPHUB_ENABLED = False
                print("❌ IPHub API key invalid - disabling IPHub service")
                return {}
            elif response.status_code == 429:
                print("⚠️ IPHub rate limit exceeded")
                return {}
            else:
                print(f"⚠️ IPHub returned status {response.status_code}")
                return {}
    except httpx.TimeoutException:
        print(f"⏰ IPHub timeout for IP {ip}")
        return {}
    except Exception as e:
        print(f"❌ IPHub error: {e}")
        return {}

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.globals['translate'] = translate
templates.env.globals['get_language_info'] = get_language_info

@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    return FileResponse("static/robots.txt", media_type="text/plain")

@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    return FileResponse("static/sitemap.xml", media_type="application/xml")

@app.get("/", response_class=HTMLResponse)
@app.get("/en/", response_class=HTMLResponse)
@app.get("/de/", response_class=HTMLResponse)
@app.get("/uk/", response_class=HTMLResponse)
@app.get("/hi/", response_class=HTMLResponse)
async def get_ip(request: Request):
    client_ip = await get_client_ip(request)
    ip_data = await fetch_ip_info(client_ip) or {}
    iphub_data = await fetch_iphub_info(client_ip) or {}
    language = get_language_from_request(request)
    return render_ip_template(request, ip_data, client_ip, iphub_data, language)

@app.get("/lookup", response_class=HTMLResponse)
@app.get("/en/lookup", response_class=HTMLResponse)
@app.get("/de/lookup", response_class=HTMLResponse)
@app.get("/uk/lookup", response_class=HTMLResponse)
@app.get("/hi/lookup", response_class=HTMLResponse)
async def lookup_ip(request: Request, ip: str = Query(...)):
    ip_data = await fetch_ip_info(ip) or {}
    iphub_data = await fetch_iphub_info(ip) or {}
    language = get_language_from_request(request)
    return render_ip_template(request, ip_data, ip, iphub_data, language)

def render_ip_template(request: Request, ip_data: dict, ip: str, iphub_data: dict = None, language: str = 'uk'):
    user_agent_str = request.headers.get("user-agent", "")
    user_agent = parse(user_agent_str)

    connection = ip_data.get("connection", {})
    security = ip_data.get("security", {})
    timezone = ip_data.get("timezone", {})
    currency = ip_data.get("currency", {})

    flag_url = f"https://flagcdn.com/256x192/{ip_data.get('country_code', '').lower()}.png" if ip_data.get("country_code") else None
    languages_raw = ip_data.get("languages", [])
    language_display = ", ".join(languages_raw) if isinstance(languages_raw, list) else str(languages_raw)

    langs = ['en', 'de', 'uk', 'hi']
    hreflang_urls = {
        lang: urljoin(str(request.base_url), f"{lang}/" if lang != 'en' else "") for lang in langs
    }

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
        "current_language": language,
        "language_info": get_language_info(language),
        "available_languages": langs,
        "page_title": translate("title", language),
        "page_description": translate("description", language),
        "hreflang_urls": hreflang_urls
    }

    return templates.TemplateResponse("index.html", context)

@app.get("/iphub-status")
async def iphub_status():
    return {
        "enabled": IPHUB_ENABLED,
        "api_key_present": bool(IPHUB_API_KEY)
    }

@app.get("/api/translations/{language}")
async def get_translations(language: str):
    if language not in ['en', 'de', 'uk', 'hi']:
        language = 'en'
    return {
        "language": language,
        "translations": TRANSLATIONS.get(language, {}),
        "language_info": get_language_info(language)
    }

@app.get("/index")
@app.get("/index.html")
async def redirect_to_main(request: Request):
    return RedirectResponse(url="/", status_code=301)
