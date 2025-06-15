from dotenv import load_dotenv
import os

load_dotenv()
IPHUB_API_KEY = os.getenv("IPHUB_API_KEY")

if not IPHUB_API_KEY:
    raise ValueError("IPHUB_API_KEY is not set. Check your .env or environment variables.")


async def fetch_iphub_info(ip: str) -> dict:
    url = f"http://v2.api.iphub.info/ip/{ip}"
    headers = {"X-Key": IPHUB_API_KEY}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"IPHub returned status {response.status_code}:{response.text}")
    except Exception as e:
        print(f"IPHub error: {e}")
    return {}

from fastapi import FastAPI, Request, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from utils.ip import get_client_ip
from user_agents import parse
import httpx

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

async def fetch_ip_info(ip: str) -> dict:
    url = f"https://ipwho.is/{ip}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()
    except httpx.HTTPError:
        return {}

@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    return FileResponse("static/robots.txt", media_type="text/plain")

@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    return FileResponse("static/sitemap.xml", media_type="application/xml")

@app.get("/", response_class=HTMLResponse)
async def get_ip(request: Request):
    client_ip = await get_client_ip(request)
    ip_data = await fetch_ip_info(client_ip) or {}
    iphub_data = await fetch_iphub_info(client_ip) or {}
    return render_ip_template(request, ip_data, client_ip, iphub_data)

@app.get("/lookup", response_class=HTMLResponse)
async def lookup_ip(request: Request, ip: str = Query(...)):
    ip_data = await fetch_ip_info(ip) or {}
    iphub_data = await fetch_iphub_info(ip) or {}
    return render_ip_template(request, ip_data, ip, iphub_data)

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
