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

    geo = requests.get(f"https://ipinfo.io/{client_ip}/json").json()

    ip_info = {
        "ip": client_ip,
        "city": geo.get("city", "Unknown"),
        "region": geo.get("region", "Unknown"),
        "country": geo.get("country", "Unknown"),
        "org": geo.get("org", "Unknown"),
        "hostname": geo.get("hostname", "Unknown"),
        "loc": geo.get("loc", ""),
    }

    return templates.TemplateResponse("index.html", {
        "request": request,
        **ip_info
    })