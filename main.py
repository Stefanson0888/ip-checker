from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
from user_agents import parse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_ip(request: Request):
    forwarded = request.headers.get("x-forwarded-for")
    client_ip = forwarded.split(",")[0] if forwarded else request.client.host

    response = requests.get(f"https://ipwho.is/{client_ip}")
    try:
        data = response.json()
        print(data)
    except ValueError:
        data = {}
        print(data)

    user_agent_string = request.headers.get("user-agent", "")
    user_agent = parse(user_agent_string)

    flag_url = f"https://flagcdn.com/256x192/{data.get('country_code','').lower()}.png" if data.get('country_code') else None

    return templates.TemplateResponse("index.html", {
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
        "timezone": data.get("timezone", "Unknown"),
        "zip": data.get("postal", "Unknown"),
        "currency": data.get("currency", {}).get("name", "Unknown"),
        "languages": data.get("languages", [{}])[0].get("name", "Unknown"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "flag_url": flag_url,
    })
