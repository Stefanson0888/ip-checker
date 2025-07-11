import httpx
import ipaddress
from fastapi import Request, HTTPException
import asyncio
from typing import Optional
import time

# Простий in-memory cache
IP_CACHE = {}
CACHE_TTL = 300  # 5 хвилин

async def get_client_ip(request: Request) -> str:
    """
    Повертає реальну IP-адресу клієнта, враховуючи проксі/Cloudflare.
    """
    # Пріоритет заголовків для отримання реального IP
    headers_to_check = [
        "cf-connecting-ip",      # Cloudflare
        "x-forwarded-for",       # Стандартний proxy header
        "x-real-ip",            # Nginx proxy
        "x-client-ip",          # Apache proxy
    ]
    
    for header in headers_to_check:
        forwarded_ip = request.headers.get(header)
        if forwarded_ip:
            # Беремо перший IP з списку (у випадку ланцюжка проксі)
            ip = forwarded_ip.split(",")[0].strip()
            try:
                # Валідуємо IP адресу
                ipaddress.ip_address(ip)
                return ip
            except ValueError:
                continue
    
    # Fallback на client.host
    return request.client.host

def validate_ip_address(ip: str) -> bool:
    """
    Перевіряє чи є рядок валідною IP адресою (IPv4 або IPv6).
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

async def fetch_ip_info(ip: str) -> dict:
    """
    Отримує інформацію про IP-адресу з кешуванням.
    """
    # Валідація IP адреси
    if not validate_ip_address(ip):
        return {"error": "Invalid IP address format"}
    
    # Перевірка кешу
    cache_key = f"ip_{ip}"
    current_time = time.time()
    
    if cache_key in IP_CACHE:
        cached_data, timestamp = IP_CACHE[cache_key]
        if current_time - timestamp < CACHE_TTL:
            return cached_data
    
    # Паралельні запити до обох API
    try:
        tasks = [
            fetch_ipwho_api(ip),
            fetch_fallback_api(ip)
        ]
        
        # Виконуємо паралельно, беремо перший успішний результат
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                if result and "error" not in result:
                    # Кешуємо результат
                    IP_CACHE[cache_key] = (result, current_time)
                    return result
            except:
                continue
        
        # Якщо всі API failed
        return {"error": "All IP APIs unavailable"}
        
    except Exception as e:
        return {"error": f"IP lookup failed: {str(e)}"}

async def fetch_ipwho_api(ip: str) -> Optional[dict]:
    """Основний API - ipwho.is"""
    try:
        url = f"https://ipwho.is/{ip}"
        async with httpx.AsyncClient(timeout=5.0) as client:  # Зменшив timeout
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("success", True):
                    return data
        return None
    except:
        return None

async def fetch_fallback_api(ip: str) -> Optional[dict]:
    """Fallback API - ip-api.com"""
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,lat,lon,timezone,isp,org,as,query,proxy,hosting"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    # Повна конвертація формату
                    return {
                        "success": True,
                        "ip": data.get("query"),
                        "type": "IPv4",
                        "continent": "Unknown",
                        "continent_code": "Unknown", 
                        "country": data.get("country", "Unknown"),
                        "country_code": data.get("countryCode", "Unknown"),
                        "region": data.get("regionName", "Unknown"),
                        "region_code": "Unknown",
                        "city": data.get("city", "Unknown"),
                        "latitude": data.get("lat"),
                        "longitude": data.get("lon"),
                        "is_eu": False,
                        "postal": "Unknown",
                        "calling_code": "Unknown",
                        "capital": "Unknown",
                        "borders": [],
                        "flag": {
                            "img": "Unknown",
                            "emoji": "Unknown",
                            "emoji_unicode": "Unknown"
                        },
                        "connection": {
                            "asn": data.get("as", "Unknown"),
                            "org": data.get("org", "Unknown"),
                            "isp": data.get("isp", "Unknown"),
                            "domain": "Unknown"
                        },
                        "timezone": {
                            "id": data.get("timezone", "Unknown"),
                            "abbr": "Unknown",
                            "is_dst": False,
                            "offset": 0,
                            "utc": "Unknown",
                            "current_time": "Unknown"
                        },
                        "security": {
                            "proxy": data.get("proxy", False),
                            "vpn": data.get("hosting", False),
                            "tor": False
                        },
                        "currency": {
                            "name": "Unknown",
                            "code": "Unknown",
                            "symbol": "Unknown",
                            "native": "Unknown",
                            "plural": "Unknown"
                        },
                        "languages": ["Unknown"]
                    }
        return None
    except:
        return None

async def fetch_ip_info_fallback(ip: str) -> dict:
    """
    Fallback API через ip-api.com (безкоштовний з лімітом 1000/хв)
    """
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,lat,lon,timezone,isp,org,as,query,proxy,hosting"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    # Конвертуємо формат ip-api.com до формату ipwho.is
                    return {
                        "success": True,
                        "ip": data.get("query"),
                        "type": "IPv4",  # ip-api.com не надає тип
                        "continent": "Unknown",
                        "continent_code": "Unknown", 
                        "country": data.get("country", "Unknown"),
                        "country_code": data.get("countryCode", "Unknown"),
                        "region": data.get("regionName", "Unknown"),
                        "region_code": "Unknown",
                        "city": data.get("city", "Unknown"),
                        "latitude": data.get("lat"),
                        "longitude": data.get("lon"),
                        "is_eu": False,
                        "postal": "Unknown",
                        "calling_code": "Unknown",
                        "capital": "Unknown",
                        "borders": [],
                        "flag": {
                            "img": "Unknown",
                            "emoji": "Unknown",
                            "emoji_unicode": "Unknown"
                        },
                        "connection": {
                            "asn": data.get("as", "Unknown"),
                            "org": data.get("org", "Unknown"),
                            "isp": data.get("isp", "Unknown"),
                            "domain": "Unknown"
                        },
                        "timezone": {
                            "id": data.get("timezone", "Unknown"),
                            "abbr": "Unknown",
                            "is_dst": False,
                            "offset": 0,
                            "utc": "Unknown",
                            "current_time": "Unknown"
                        },
                        "security": {
                            "proxy": data.get("proxy", False),
                            "vpn": data.get("hosting", False),  # ip-api використовує hosting як VPN/proxy
                            "tor": False
                        },
                        "currency": {
                            "name": "Unknown",
                            "code": "Unknown",
                            "symbol": "Unknown",
                            "native": "Unknown",
                            "plural": "Unknown"
                        },
                        "languages": ["Unknown"]
                    }
                else:
                    return {"error": data.get("message", "Fallback API error")}
            else:
                return {"error": f"Fallback API returned status {response.status_code}"}
                
    except Exception as e:
        return {"error": f"Fallback API error: {str(e)}"}