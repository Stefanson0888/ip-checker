from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests

app = FastAPI()

# Підключення папок
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_ip(request: Request):
    # Отримання IP-адреси користувача
    forwarded = request.headers.get("x-forwarded-for")
    client_ip = forwarded.split(",")[0] if forwarded else request.client.host

    # Запит до IPWhois API
    try:
        response = requests.get(f"https://ipwhois.io/json/{client_ip}")
        if response.status_code == 200:
            data = response.json()
            if not data.get("success", True):  # деякі відповіді можуть мати success=False
                data = {}
        else:
            data = {}
    except Exception as e:
        print(f"Error fetching IP data: {e}")
        data = {}

    # Формування URL прапора (якщо є код країни)
    flag_url = None
    if data.get("country_code"):
        flag_url = f"https://flagcdn.com/256x192/{data['country_code'].lower()}.png"

    # Рендер сторінки
    return templates.TemplateResponse("index.html", {
        "request": request,
        "ip": client_ip,
        "city": data.get("city", "Unknown"),
        "region": data.get("region", "Unknown"),
        "country": data.get("country", "Unknown"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "flag_url": flag_url,
    })
