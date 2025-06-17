from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import httpx
import json
import os
from pathlib import Path

app = FastAPI()

# Завантаження перекладів
def load_translations():
    """Завантажуємо всі переклади з папки locales"""
    translations = {}
    locales_dir = Path("locales")
    
    if not locales_dir.exists():
        print("⚠️ Папка locales не знайдена! Створіть її з файлами перекладів")
        return {"en": {}, "uk": {}, "de": {}, "hi": {}}
    
    for lang in ['en', 'de', 'uk', 'hi']:
        lang_file = locales_dir / lang / "messages.json"
        if lang_file.exists():
            with open(lang_file, 'r', encoding='utf-8') as f:
                translations[lang] = json.load(f)
        else:
            print(f"⚠️ Файл {lang_file} не знайдено")
            translations[lang] = {}
    
    return translations

# Завантажуємо переклади при старті
TRANSLATIONS = load_translations()

def get_language(request: Request) -> str:
    """Визначаємо мову користувача"""
    # Спочатку перевіряємо URL шлях
    path = request.url.path
    if path.startswith('/de/') or path == '/de':
        return 'de'
    if path.startswith('/uk/') or path == '/uk': 
        return 'uk'
    if path.startswith('/hi/') or path == '/hi':
        return 'hi'
    
    # Потім дивимось на заголовок Accept-Language
    accept_lang = request.headers.get('accept-language', '').lower()
    if 'de' in accept_lang:
        return 'de'
    if 'uk' in accept_lang:
        return 'uk' 
    if 'hi' in accept_lang:
        return 'hi'
    
    # За замовчуванням - англійська
    return 'en'

def translate(key: str, lang: str) -> str:
    """Функція для перекладу тексту"""
    return TRANSLATIONS.get(lang, {}).get(key, key)

def get_ip_info(ip: str):
    """Отримуємо інформацію про IP"""
    try:
        # Ваш існуючий код для отримання IP інформації
        response = httpx.get(f"http://ip-api.com/json/{ip}")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Помилка отримання IP інформації: {e}")
    return {}

def get_iphub_info(ip: str):
    """Отримуємо інформацію з IPHub (VPN/Proxy detection)"""
    try:
        headers = {"X-Key": "YOUR_IPHUB_API_KEY"}  # Замініть на ваш ключ
        response = httpx.get(f"http://v2.api.iphub.info/ip/{ip}", headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Помилка IPHub: {e}")
    return {}

def generate_html(ip_data: dict, ip: str, iphub_data: dict, lang: str) -> str:
    """Генеруємо HTML з перекладами"""
    
    # Функція для безпечного отримання значень
    def safe_get(data, key, default="Unknown"):
        return data.get(key, default) if data else default
    
    # Перекладаємо булеві значення
    def translate_bool(value):
        if value is True:
            return "True" 
        elif value is False:
            return "False"
        return translate("unknown", lang)
    
    html = f"""
    <!DOCTYPE html>
    <html lang="{lang}">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{translate('title', lang)}</title>
        <meta name="description" content="{translate('description', lang)}">
        
        <!-- SEO теги для різних мов -->
        <link rel="alternate" hreflang="en" href="https://yoursite.com/">
        <link rel="alternate" hreflang="de" href="https://yoursite.com/de/">
        <link rel="alternate" hreflang="uk" href="https://yoursite.com/uk/">
        <link rel="alternate" hreflang="hi" href="https://yoursite.com/hi/">
        
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .ip-address {{
                font-size: 2em;
                font-weight: bold;
                color: #2563eb;
                text-align: center;
                margin: 20px 0;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-top: 20px;
            }}
            .info-item {{
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
            }}
            .info-label {{
                font-weight: bold;
                color: #6b7280;
                font-size: 0.9em;
            }}
            .info-value {{
                margin-top: 5px;
                font-size: 1.1em;
            }}
            .language-switcher {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .language-switcher a {{
                margin: 0 10px;
                text-decoration: none;
                padding: 5px 10px;
                border-radius: 5px;
                background: #e5e7eb;
            }}
            .language-switcher a.active {{
                background: #2563eb;
                color: white;
            }}
            @media (max-width: 600px) {{
                .info-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Перемикач мов -->
            <div class="language-switcher">
                <a href="/" {"class='active'" if lang == 'en' else ""}>🇺🇸 EN</a>
                <a href="/de/" {"class='active'" if lang == 'de' else ""}>🇩🇪 DE</a>
                <a href="/uk/" {"class='active'" if lang == 'uk' else ""}>🇺🇦 UK</a>
                <a href="/hi/" {"class='active'" if lang == 'hi' else ""}>🇮🇳 HI</a>
            </div>
            
            <h1>{translate('title', lang)}</h1>
            
            <div class="ip-address">{translate('your_ip', lang)}: {ip}</div>
            
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">{translate('city', lang)}</div>
                    <div class="info-value">{safe_get(ip_data, 'city')}</div>
                </div>
                
                <div class="info-item">
                    <div class="info-label">{translate('region', lang)}</div>
                    <div class="info-value">{safe_get(ip_data, 'regionName')}</div>
                </div>
                
                <div class="info-item">
                    <div class="info-label">{translate('country', lang)}</div>
                    <div class="info-value">{safe_get(ip_data, 'country')}</div>
                </div>
                
                <div class="info-item">
                    <div class="info-label">{translate('ip_type', lang)}</div>
                    <div class="info-value">IPv4</div>
                </div>
                
                <div class="info-item">
                    <div class="info-label">{translate('isp', lang)}</div>
                    <div class="info-value">{safe_get(ip_data, 'isp')}</div>
                </div>
                
                <div class="info-item">
                    <div class="info-label">{translate('organization', lang)}</div>
                    <div class="info-value">{safe_get(ip_data, 'org')}</div>
                </div>
                
                <div class="info-item">
                    <div class="info-label">{translate('timezone', lang)}</div>
                    <div class="info-value">{safe_get(ip_data, 'timezone')}</div>
                </div>
                
                <div class="info-item">
                    <div class="info-label">{translate('postal_code', lang)}</div>
                    <div class="info-value">{safe_get(ip_data, 'zip')}</div>
                </div>
                
                <div class="info-item">
                    <div class="info-label">{translate('vpn', lang)}</div>
                    <div class="info-value">{translate_bool(iphub_data.get('block') == 1)}</div>
                </div>
                
                <div class="info-item">
                    <div class="info-label">{translate('proxy', lang)}</div>
                    <div class="info-value">{translate_bool(iphub_data.get('block') == 1)}</div>
                </div>
            </div>
        </div>
        
        <!-- Google Analytics (додайте свій код) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());
            gtag('config', 'GA_MEASUREMENT_ID');
        </script>
    </body>
    </html>
    """
    return html

# Маршрути для різних мов
@app.get("/", response_class=HTMLResponse)
@app.get("/en/", response_class=HTMLResponse) 
@app.get("/de/", response_class=HTMLResponse)
@app.get("/uk/", response_class=HTMLResponse)
@app.get("/hi/", response_class=HTMLResponse)
async def get_ip(request: Request):
    """Головна сторінка з визначенням мови"""
    
    # Отримуємо IP користувача
    client_ip = request.client.host
    if client_ip == "127.0.0.1":
        # Для локального тестування використовуємо зовнішній IP
        try:
            response = httpx.get("https://httpbin.org/ip")
            client_ip = response.json().get("origin", "").split(",")[0].strip()
        except:
            client_ip = "8.8.8.8"  # Fallback IP
    
    # Визначаємо мову
    language = get_language(request)
    
    # Отримуємо дані про IP
    ip_data = get_ip_info(client_ip)
    iphub_data = get_iphub_info(client_ip)
    
    # Генеруємо і повертаємо HTML
    html_content = generate_html(ip_data, client_ip, iphub_data, language)
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)