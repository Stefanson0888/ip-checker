import httpx
import ipaddress
from fastapi import Request, HTTPException

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
    Отримує інформацію про IP-адресу через API ipwho.is.
    """
    # Валідація IP адреси
    if not validate_ip_address(ip):
        return {"error": "Invalid IP address format"}
    
    url = f"https://ipwho.is/{ip}"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                # Перевіряємо чи API повернув success
                if data.get("success", True):
                    return data
                else:
                    return {"error": data.get("message", "API returned error")}
            else:
                return {"error": f"API returned status {response.status_code}"}
                
    except httpx.TimeoutException:
        return {"error": "Request timeout"}
    except httpx.HTTPError as e:
        return {"error": f"HTTP error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}