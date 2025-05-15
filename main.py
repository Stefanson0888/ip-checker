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

    geo = requests.get(f"https://ipapi.co/{client_ip}/json/").json()

    ip_info = {
        "ip": client_ip,
        "city": geo.get("city", "Unknown"),
        "region": geo.get("region", "Unknown"),
        "country": geo.get("country_name", "Unknown"),
        "country_code": geo.get("country_code", "xx"),
        "latitude": geo.get("latitude", ""),
        "longitude": geo.get("longitude", ""),
        "org": geo.get("org", "Unknown"),
        "flag_url": f"https://flagcdn.com/256x192/{geo.get('country_code', 'xx').lower()}.png"
    }

    return templates.TemplateResponse("index.html", {
        "request": request,
        **ip_info
    })
