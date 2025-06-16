from dotenv import load_dotenv
import os
import httpx
import re
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import FastAPI, Request, Query, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from utils.ip import get_client_ip, fetch_ip_info
from user_agents import parse

load_dotenv()
IPHUB_API_KEY = os.getenv("IPHUB_API_KEY")
IPHUB_ENABLED = bool(IPHUB_API_KEY)

# -----------------------------
# Rate Limiter
# -----------------------------
limiter = Limiter(key_func=get_remote_address)

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda r, e: JSONResponse(
    status_code=429, content={"detail": "Too many requests"}
))

# -----------------------------
# Middleware
# -----------------------------
app.add_middleware(HTTPSRedirectMiddleware)  # redirect HTTP -> HTTPS
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.app", "www.yourdomain.app", "127.0.0.1", "localhost"]  # ❗ Заміни на свій домен
)

# -----------------------------
# Static & Templates
# -----------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# -----------------------------
# IPHub fetch
# -----------------------------
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

# -----------------------------
# Routes
# -----------------------------
@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    return FileResponse("static/robots.txt", media_type="text/plain")

@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    return FileResponse("static/sitemap.xml", media_type="application/xml")

@app.get("/", response_class=HTMLResponse)
@limiter.limit("30/minute")
async def get_ip(request: Request):
    client_ip = await get_client_ip(request)
    ip_data = await fetch_ip_info(client_ip) or {}
    iphub_data = await fetch_iphub_info(client_ip) or {}
    return render_ip_template(request, ip_data, client_ip, iphub_data)

@app.get("/lookup", response_class=HTMLResponse)
@limiter.limit("30/minute")
async def lookup_ip(request: Request, ip: str = Query(...)):
    # 🔐 Валідація IP
    if not re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", ip):
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "Invalid IP format"})

    ip_data = await fetch_ip_info(ip) or {}
    iphub_data = await fetch_iphub_info(ip) or {}
    return render_ip_template(request, ip_data, ip, iphub_data)

@app.get("/iphub-status")
async def iphub_status():
    return {"enabled": IPHUB_ENABLED, "api_key_present": bool(IPHUB_API_KEY)}

# -----------------------------
# Template Renderer
# -----------------------------
def render_ip_template(request: Request, ip_data: dict, ip: str, iphub_data: dict = None):
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
    language = ", ".join(languages_raw) if isinstance(languages_raw, list) else str(languages_raw)

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
        "language": language,
        "flag_url": flag_url,
        "iphub_block": iphub_data.get("block") if iphub_data else None,
        "iphub_isp": iphub_data.get("isp") if iphub_data else None,
        "iphub_hostname": iphub_data.get("hostname") if iphub_data else None,
    }

    return templates.TemplateResponse("index.html", context)
