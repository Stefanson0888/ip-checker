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

    response = requests.get(f"https://ipapi.co/{client_ip}/json/")
    data = response.json()

    flag_url = f"https://flagcdn.com/256x192/{data.get('country_code','').lower()}.png" if data.get('country_code') else None

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
