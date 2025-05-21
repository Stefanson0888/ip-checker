from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from user_agents import parse
import httpx
import logging

app = FastAPI()

# Логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Папки
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Запит до IP API
async def fetch_ip_info(client_ip: str) -> dict:
    url = f"https://ipwho.is/{client_ip}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            data = response.json()
            if not data.get("success", False):
                logger.warning(f"IP API returned success=False for IP {client_ip}")
                return {}
            return data
    except Exception as e:
        logger.error(f"Error fetching IP info: {e}")
        return {}

# Головна сторінка
@app.get("/", response_class=HTMLResponse)
async def get_ip(request: Request):
    # Отримуємо IP клієнта
    forwarded = request.headers.get("x-forwarded-for")
    client_ip = forwarded.split(",")[0] if forwarded else request.client.host

    # Отримуємо дані про IP
    data = await fetch_ip_info(client_ip)

    # Парсимо User-Agent
    user_agent_string = request.headers.get("user-agent", "")
    user_agent = parse(user_agent_string)

    # URL прапора
    flag_url = f"https://flagcdn.com/256x192/{data.get('country_code', '').lower()}.png" if data.get("country_code") else None

    # Часовий пояс
    timezone = data.get("timezone", {})

    # Формування контексту
    context = {
        "request": request,
        "ip": client_ip,
        "type": data.get("type", "Unknown"),
        "isp": data.get("connection", {}).get("isp", "Unknown"),
        "asn": data.get("connection", {}).get("asn", "Unknown"),
        "hostname": data.get("connection", {}).get("domain", "Unknown"),
        "is_proxy": data.get("security", {}).get("proxy", False),
        "is_vpn": data.get("security", {}).get("vpn", False),
        "is_tor": data.get("security", {}).get("tor", False),
        "user_agent": user_agent_string,
        "browser": user_agent.browser.family,
        "os": user_agent.os.family,
        "city": data.get("city", "Unknown"),
        "region": data.get("region", "Unknown"),
        "country": data.get("country", "Unknown"),
        "country_code": data.get("country_code", "Unknown"),
        "postal": data.get("postal", "Unknown"),
        "calling_code": data.get("calling_code", "Unknown"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "timezone": timezone.get("id", "Unknown"),
        "currency": data.get("currency", {}).get("code", "Unknown"),
        "language": ", ".join(data.get("languages", "").split(",")) if data.get("languages") else "Unknown",
        "flag_url": flag_url,
    }

    return templates.TemplateResponse("index.html", context)
