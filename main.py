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
from affiliate_config import AFFILIATE_URLS, get_nordvpn_url, get_nordpass_url

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Redirect middleware - з render домену на основний
@app.middleware("http")
async def redirect_render_domain(request: Request, call_next):
    """Перенаправляє traffic з render домену на основний checkip.app"""
    host = str(request.url).replace("://", "").split("/")[0]
    
    if "onrender.com" in host:
        # Створюємо URL з основним доменом
        new_url = str(request.url).replace(host, "checkip.app")
        return RedirectResponse(url=new_url, status_code=301)
    
    response = await call_next(request)
    return response


@app.get("/robots.txt", include_in_schema=False)


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

@app.post("/api/track-event")
async def track_custom_event(request: Request):
    """API endpoint для додаткового серверного трекінгу"""
    try:
        data = await request.json()
        client_ip = await get_client_ip(request)
        
        # Логування події для аналізу
        event_info = {
            'event': data.get('event'),
            'category': data.get('event_category'),
            'label': data.get('event_label'),
            'language': data.get('language'),
            'ip': client_ip,
            'timestamp': data.get('timestamp')
        }
        
        print(f"📊 Custom Event: {event_info}")
        
        return {"status": "success", "message": "Event tracked successfully"}
    except Exception as e:
        print(f"❌ Custom tracking error: {e}")
        return {"status": "error", "message": "Failed to track event"}

# What Is My IP - SEO landing page
@app.get("/what-is-my-ip", response_class=HTMLResponse)
async def what_is_my_ip(request: Request):
    client_ip = await get_client_ip(request)
    ip_data = await fetch_ip_info(client_ip)
    
    if "error" in ip_data:
        ip_data = {"error": ip_data["error"]}
    
    iphub_data = await fetch_iphub_info(client_ip)
    
    # Використовуємо ту ж логіку що й у render_ip_template
    user_agent_str = request.headers.get("user-agent", "")
    user_agent = parse(user_agent_str)
    
    # Детекція tech користувача
    is_tech_user = False
    referrer = request.headers.get("referer", "").lower()
    tech_user_agents = [
        'developer', 'github', 'vscode', 'postman', 'curl', 'wget', 
        'insomnia', 'httpie', 'python-requests', 'node', 'npm'
    ]
    tech_referrers = [
        'github.com', 'stackoverflow.com', 'aws.amazon.com', 
        'digitalocean.com', 'hetzner.com', 'cloudflare.com',
        'netlify.com', 'vercel.com', 'heroku.com'
    ]
    
    is_tech_user = (
        any(term in user_agent_str.lower() for term in tech_user_agents) or
        any(term in referrer for term in tech_referrers)
    )
    
    # Обробка даних
    connection = ip_data.get("connection", {})
    security = ip_data.get("security", {})
    
    context = {
        "request": request,
        "ip": client_ip,
        "city": ip_data.get("city", "Unknown"),
        "country": ip_data.get("country", "Unknown"),  
        "isp": connection.get("isp", "Unknown"),
        "is_vpn": security.get("vpn", False),
        "type": ip_data.get("type", "IPv4"),
        "gtm_id": GTM_ID,
        "is_tech_user": is_tech_user
    }
    
    return templates.TemplateResponse("what-is-my-ip.html", context)

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


# IP Lookup Tool - англійська за замовчуванням  
@app.get("/ip-lookup-tool", response_class=HTMLResponse)
async def ip_lookup_tool_default(request: Request):
    return await ip_lookup_tool_page(request, DEFAULT_LANGUAGE)

# IP Lookup Tool - мовні версії
@app.get("/{lang}/ip-lookup-tool", response_class=HTMLResponse) 
async def ip_lookup_tool_with_lang(request: Request, lang: str):
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=404, detail="Language not supported")
    return await ip_lookup_tool_page(request, lang)

async def ip_lookup_tool_page(request: Request, lang: str):
    """Render IP Lookup Tool page"""
    _ = Translator(lang)

    context = {
        "request": request,
        "lang": lang,
        "_": _,
        "language_urls": get_language_urls("/ip-lookup-tool", lang),
        "hreflang_urls": get_hreflang_urls(str(request.base_url), "/ip-lookup-tool"),
        "base_url": str(request.base_url).rstrip('/'),
        "google_analytics_id": GOOGLE_ANALYTICS_ID,
        "gtm_id": GTM_ID
    }

    return templates.TemplateResponse("ip-lookup-tool.html", context)


# VPN Detection - English (default)
@app.get("/am-i-using-vpn")
async def vpn_detection_en(request: Request):
    return await vpn_detection_page(request, "en")

# VPN Detection - German  
@app.get("/de/am-i-using-vpn")
async def vpn_detection_de(request: Request):
    return await vpn_detection_page(request, "de")

# VPN Detection - Polish
@app.get("/pl/am-i-using-vpn") 
async def vpn_detection_pl(request: Request):
    return await vpn_detection_page(request, "pl")

# VPN Detection - Hindi
@app.get("/hi/am-i-using-vpn")
async def vpn_detection_hi(request: Request):
    return await vpn_detection_page(request, "hi")

# VPN Detection - Ukrainian
@app.get("/uk/am-i-using-vpn")
async def vpn_detection_uk(request: Request):
    return await vpn_detection_page(request, "uk")

# VPN Detection main function
async def vpn_detection_page(request: Request, lang: str):
    try:
        # Get user IP (використовуємо існуючу функцію)
        user_ip = await get_client_ip(request)
        
        # Get IP information (використовуємо існуючу функцію)
        ip_data = await fetch_ip_info(user_ip)
        
        # VPN Detection using IPHub
        is_vpn = False
        iphub_data = {}
        
        #  перевіряємо security з основного API
        if not ("error" in ip_data):
            security = ip_data.get('security', {})
            is_vpn = security.get('vpn', False) or security.get('proxy', False)
        
        # додаємо IPHub detection
        try:
            iphub_data = await fetch_iphub_info(user_ip)
            if iphub_data and iphub_data.get('block') == 1:
                is_vpn = True
        except:
            pass
        
        # Get location info
        user_location = "Unknown"
        user_isp = "Unknown"
        
        if not ("error" in ip_data):
            city = ip_data.get('city', 'Unknown')
            country = ip_data.get('country', 'Unknown')
            user_location = f"{city}, {country}"
            
            connection = ip_data.get('connection', {})
            user_isp = connection.get('isp', 'Unknown')
        
        # Get affiliate URLs
        nordvpn_url = get_nordvpn_url("vpn_detection", "main_cta")
        nordpass_url = get_nordpass_url("vpn_detection", "password_manager")
        
        # Create translator
        translator = Translator(lang)
        
        # Get language URLs for navigation
        current_path = f"/{lang}/am-i-using-vpn" if lang != "en" else "/am-i-using-vpn"
        language_urls = get_language_urls(current_path, lang)
        
        # Get hreflang URLs for SEO
        base_url = str(request.base_url).rstrip('/')
        hreflang_urls = get_hreflang_urls(base_url, current_path)
        
        # Template context
        context = {
            "request": request,
            "lang": lang,
            "supported_languages": SUPPORTED_LANGUAGES,
            "_": translator,
            
            # VPN Detection data
            "user_ip": user_ip,
            "is_vpn": is_vpn,
            "iphub_data": iphub_data,
            "user_location": user_location,
            "user_isp": user_isp,
            
            # Affiliate URLs
            "nordvpn_url": nordvpn_url,
            "nordpass_url": nordpass_url,
            
            # SEO and navigation
            "current_path": current_path,
            "language_urls": language_urls,
            "hreflang_urls": hreflang_urls,
            "base_url": base_url,
            "gtm_id": GTM_ID,
            "google_analytics_id": GOOGLE_ANALYTICS_ID,
        }
        
        return templates.TemplateResponse("am-i-using-vpn.html", context)
        
    except Exception as e:
        print(f"Error in VPN detection page: {e}")
        # Fallback to error page or redirect to home
        if lang != "en":
            return RedirectResponse(url=f"/{lang}/")
        else:
            return RedirectResponse(url="/")

# Optional: API endpoint for VPN check (for future use)
@app.get("/api/vpn-check")
async def api_vpn_check(request: Request):
    """API endpoint for VPN detection"""
    try:
        user_ip = await get_client_ip(request)
        ip_data = await fetch_ip_info(user_ip)
        
        is_vpn = False
        if not ("error" in ip_data):
            security = ip_data.get('security', {})
            is_vpn = security.get('vpn', False) or security.get('proxy', False)
            
            # Додаткова перевірка з IPHub
            try:
                iphub_data = await fetch_iphub_info(user_ip)
                if iphub_data and iphub_data.get('block') == 1:
                    is_vpn = True
            except:
                pass
            
        return {
            "ip": user_ip,
            "is_vpn": is_vpn,
            "location": f"{ip_data.get('city', 'Unknown')}, {ip_data.get('country', 'Unknown')}" if not ("error" in ip_data) else "Unknown",
            "isp": ip_data.get('connection', {}).get('isp', 'Unknown') if not ("error" in ip_data) else "Unknown",
            "status": "success"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }