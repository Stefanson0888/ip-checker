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

    try:
        response = requests.get(f"https://ipapi.co/{client_ip}/json/")
        if response.status_code == 200:
            data = response.json()
        else:
            data = {}
    except Exception as e:
        print(f"Error fetching IP data: {e}")
        data = {}

    country_code = data.get("country_code")
    flag_url = f"https://flagcdn.com/256x192/{country_code.lower()}.png" if country_code else None

    return templates.TemplateResponse("index.html", {
        "request": request,
        "ip": client_ip,
        "city": data.get("city", "Unknown"),
        "region": data.get("region", "Unknown"),
        "country": data.get("country_name", "Unknown"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "flag_url": flag_url,
    })
