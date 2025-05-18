from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_ip(request: Request):
    forwarded = request.headers.get("x-forwarded-for")
    client_ip = forwarded.split(",")[0] if forwarded else request.client.host

    user_agent = request.headers.get("user-agent", "Unknown")

    # Отримуємо дані з ipwho.is
    response = requests.get(f"https://ipwho.is/{client_ip}")
    try:
        data = response.json()
    except ValueError:
        data = {}

    # Прапор
    flag_url = f"https://flagcdn.com/256x192/{data.get('country_code','').lower()}.png" if data.get('country_code') else None

    # Підготовка даних для шаблону
    return templates.TemplateResponse("index.html", {
        "request": request,
        "ip": client_ip,
        "ip_type": data.get("type", "Unknown"),
        "city": data.get("city", "Unknown"),
        "region": data.get("region", "Unknown"),
        "country": data.get("country", "Unknown"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "flag_url": flag_url,
        "isp": data.get("connection", {}).get("isp", "Unknown"),
        "asn": data.get("connection", {}).get("asn", "Unknown"),
        "org": data.get("connection", {}).get("org", "Unknown"),
        "user_agent": user_agent,
    })
