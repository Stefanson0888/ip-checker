from dotenv import load_dotenv
import os
import httpx 
import ipaddress

load_dotenv()
IPHUB_API_KEY = os.getenv("IPHUB_API_KEY")
GOOGLE_ANALYTICS_ID = os.getenv("GOOGLE_ANALYTICS_ID", "G-525FX5C7Z8")
GTM_ID = os.getenv("GTM_ID", "GTM-WN4J2JQW")
IPHUB_ENABLED = bool(IPHUB_API_KEY)

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
                print(f"❌ IPHub API key invalid - disabling IPHub service")
                return {}
            elif response.status_code == 429:
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

from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from utils.ip import get_client_ip, fetch_ip_info, validate_ip_address
from utils.i18n import (
    get_language_from_request, get_language_from_path, 
    Translator, get_language_urls, get_hreflang_urls,
    SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
)
from user_agents import parse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    return FileResponse("static/robots.txt", media_type="text/plain")

@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    return FileResponse("static/sitemap.xml", media_type="application/xml")

@app.get("/ads.txt", include_in_schema=False)
async def ads_txt():
    return FileResponse("static/ads.txt", media_type="text/plain")

# Головна сторінка (англійська за замовчуванням)
@app.get("/", response_class=HTMLResponse)
async def get_ip_default(request: Request):
    return await get_ip_with_language(request, DEFAULT_LANGUAGE)

# Мовні версії головної сторінки
@app.get("/{lang}/", response_class=HTMLResponse)
async def get_ip_with_lang(request: Request, lang: str):
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=404, detail="Language not supported")
    return await get_ip_with_language(request, lang)

async def get_ip_with_language(request: Request, lang: str):
    client_ip = await get_client_ip(request)
    ip_data = await fetch_ip_info(client_ip)
    
    if "error" in ip_data:
        ip_data = {"error": ip_data["error"]}
    
    iphub_data = await fetch_iphub_info(client_ip)
    return render_ip_template(request, ip_data, client_ip, iphub_data, lang)

# Lookup (англійська за замовчуванням)
@app.get("/lookup", response_class=HTMLResponse)
async def lookup_ip_default(request: Request, ip: str = Query(...)):
    return await lookup_ip_with_language(request, ip, DEFAULT_LANGUAGE)

# Мовні версії lookup
@app.get("/{lang}/lookup", response_class=HTMLResponse)
async def lookup_ip_with_lang(request: Request, lang: str, ip: str = Query(...)):
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=404, detail="Language not supported")
    return await lookup_ip_with_language(request, ip, lang)

async def lookup_ip_with_language(request: Request, ip: str, lang: str):
    if not validate_ip_address(ip):
        raise HTTPException(status_code=400, detail="Invalid IP address format")
    
    ip_data = await fetch_ip_info(ip)
    
    if "error" in ip_data:
        ip_data = {"error": ip_data["error"]}
    
    iphub_data = await fetch_iphub_info(ip)
    return render_ip_template(request, ip_data, ip, iphub_data, lang)

def render_ip_template(request: Request, ip_data: dict, ip: str, iphub_data: dict = None, lang: str = DEFAULT_LANGUAGE):
    user_agent_str = request.headers.get("user-agent", "")
    user_agent = parse(user_agent_str)

    
    # Детекція типу користувача для персоналізованої реклами
    is_tech_user = False
    referrer = request.headers.get("referer", "").lower()
    
    # Перевіряємо User-Agent на ознаки розробника
    tech_user_agents = [
        'developer', 'github', 'vscode', 'postman', 'curl', 'wget', 
        'insomnia', 'httpie', 'python-requests', 'node', 'npm'
    ]
    
    # Перевіряємо Referer на tech сайти
    tech_referrers = [
        'github.com', 'stackoverflow.com', 'aws.amazon.com', 
        'digitalocean.com', 'hetzner.com', 'cloudflare.com',
        'netlify.com', 'vercel.com', 'heroku.com'
    ]
    
    # Детекція tech користувача
    is_tech_user = (
        any(term in user_agent_str.lower() for term in tech_user_agents) or
        any(term in referrer for term in tech_referrers)
    )
    
    # Створюємо об'єкт для перекладів
    _ = Translator(lang)

    # Обробка помилок API
    if "error" in ip_data:
        context = {
            "request": request,
            "ip": ip,
            "error": ip_data["error"],
            "user_agent": user_agent_str,
            "browser": user_agent.browser.family,
            "os": user_agent.os.family,
            "lang": lang,
            "_": _,
            "language_urls": get_language_urls(str(request.url.path), lang),
            "hreflang_urls": get_hreflang_urls(str(request.base_url), str(request.url.path)),
            "google_analytics_id": GOOGLE_ANALYTICS_ID,
            "gtm_id": GTM_ID,
            "is_tech_user": is_tech_user,
            "country_code": ip_data.get("country_code", "Unknown"),
            "security": {},  # Порожній для error page
        }
        return templates.TemplateResponse("error.html", context)

    connection = ip_data.get("connection", {})
    security = ip_data.get("security", {})
    timezone = ip_data.get("timezone", {})
    currency = ip_data.get("currency", {})

    flag_url = (
        f"https://flagcdn.com/256x192/{ip_data.get('country_code', '').lower()}.png"
        if ip_data.get("country_code") else None
    )

    languages_raw = ip_data.get("languages", [])
    language = ", ".join(languages_raw) if isinstance(languages_raw, list) else str(languages_raw)

    context = {
        "request": request,
        "ip": ip,
        "type": ip_data.get("type", _("unknown")),
        "isp": connection.get("isp", _("unknown")),
        "asn": connection.get("asn", _("unknown")),
        "hostname": connection.get("domain", _("unknown")),
        "is_proxy": security.get("proxy", False),
        "is_vpn": security.get("vpn", False),
        "is_tor": security.get("tor", False),
        "user_agent": user_agent_str,
        "browser": user_agent.browser.family,
        "os": user_agent.os.family,
        "city": ip_data.get("city", _("unknown")),
        "region": ip_data.get("region", _("unknown")),
        "country": ip_data.get("country", _("unknown")),
        "country_code": ip_data.get("country_code", _("unknown")),
        "postal": ip_data.get("postal", _("unknown")),
        "calling_code": ip_data.get("calling_code", _("unknown")),
        "latitude": ip_data.get("latitude"),
        "longitude": ip_data.get("longitude"),
        "timezone": timezone.get("id", _("unknown")),
        "currency": currency.get("code", _("unknown")),
        "language": language,
        "flag_url": flag_url,
        "iphub_block": iphub_data.get("block") if iphub_data else None,
        "iphub_isp": iphub_data.get("isp") if iphub_data else None,
        "iphub_hostname": iphub_data.get("hostname") if iphub_data else None,
        # i18n контекст
        "lang": lang,
        "_": _,
        "language_urls": get_language_urls(str(request.url.path), lang),
        "hreflang_urls": get_hreflang_urls(str(request.base_url), str(request.url.path)),
        "is_tech_user": is_tech_user,
        "security": security,  # Для conditional security widgets
        "google_analytics_id": GOOGLE_ANALYTICS_ID,
        "gtm_id": GTM_ID
    }

    return templates.TemplateResponse("index.html", context)

@app.get("/iphub-status")
async def iphub_status():
    return {
        "enabled": IPHUB_ENABLED,
        "api_key_present": bool(IPHUB_API_KEY)
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "IP Checker"}

# Analytics endpoint для відстеження подій
@app.post("/analytics/event")
async def track_event(request: Request):
    """Endpoint для додаткового трекінгу подій"""
    try:
        data = await request.json()
        # Тут можна додати серверний трекінг або логування
        print(f"📊 Analytics event: {data}")
        return {"status": "success"}
    except Exception as e:
        print(f"❌ Analytics error: {e}")
        return {"status": "error"}

# Privacy Policy - англійська за замовчуванням  
@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy_default(request: Request):
    return await privacy_policy_with_language(request, DEFAULT_LANGUAGE)

# Privacy Policy - мовні версії
@app.get("/{lang}/privacy", response_class=HTMLResponse) 
async def privacy_policy_with_lang(request: Request, lang: str):
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=404, detail="Language not supported")
    return await privacy_policy_with_language(request, lang)

async def privacy_policy_with_language(request: Request, lang: str):
    """Render Privacy Policy page"""
    _ = Translator(lang)
    
    context = {
        "request": request,
        "lang": lang,
        "_": _,
        "language_urls": get_language_urls("/privacy", lang),
        "hreflang_urls": get_hreflang_urls(str(request.base_url), "/privacy"),
        "google_analytics_id": GOOGLE_ANALYTICS_ID,
        "gtm_id": GTM_ID
    }
    
    return templates.TemplateResponse("privacy.html", context)

# Terms of Service - англійська за замовчуванням  
@app.get("/terms", response_class=HTMLResponse)
async def terms_of_service_default(request: Request):
    return await terms_of_service_with_language(request, DEFAULT_LANGUAGE)

# Terms of Service - мовні версії
@app.get("/{lang}/terms", response_class=HTMLResponse) 
async def terms_of_service_with_lang(request: Request, lang: str):
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=404, detail="Language not supported")
    return await terms_of_service_with_language(request, lang)

async def terms_of_service_with_language(request: Request, lang: str):
    """Render Terms of Service page"""
    _ = Translator(lang)
    
    context = {
        "request": request,
        "lang": lang,
        "_": _,
        "language_urls": get_language_urls("/terms", lang),
        "hreflang_urls": get_hreflang_urls(str(request.base_url), "/terms"),
        "google_analytics_id": GOOGLE_ANALYTICS_ID,
        "gtm_id": GTM_ID
    }
    
    return templates.TemplateResponse("terms.html", context)

# Contact - англійська за замовчуванням  
@app.get("/contact", response_class=HTMLResponse)
async def contact_default(request: Request):
    return await contact_with_language(request, DEFAULT_LANGUAGE)

# Contact - мовні версії
@app.get("/{lang}/contact", response_class=HTMLResponse) 
async def contact_with_lang(request: Request, lang: str):
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=404, detail="Language not supported")
    return await contact_with_language(request, lang)

async def contact_with_language(request: Request, lang: str):
    """Render Contact page"""
    _ = Translator(lang)
    
    context = {
        "request": request,
        "lang": lang,
        "_": _,
        "language_urls": get_language_urls("/contact", lang),
        "hreflang_urls": get_hreflang_urls(str(request.base_url), "/contact"),
        "google_analytics_id": GOOGLE_ANALYTICS_ID,
        "gtm_id": GTM_ID
    }
    
    return templates.TemplateResponse("contact.html", context)