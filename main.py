
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

@app.route("/")
def index():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/")
        data = response.json()
    except Exception:
        data = {}

    country_code = data.get("country_code", "").lower()
    flag_url = f"https://flagcdn.com/256x192/{country_code}.png" if country_code else ""

    return render_template("index.html",
                           ip=ip,
                           city=data.get("city", "Unknown"),
                           region=data.get("region", "Unknown"),
                           country=data.get("country_name", "Unknown"),
                           latitude=data.get("latitude"),
                           longitude=data.get("longitude"),
                           flag_url=flag_url)
