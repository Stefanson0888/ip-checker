import httpx
from fastapi import Request

async def get_client_ip(request: Request) -> str:
    """
    Повертає реальну IP-адресу клієнта, враховуючи проксі/Cloudflare.
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    return forwarded_for.split(",")[0] if forwarded_for else request.client.host

async def fetch_ip_info(ip: str) -> dict:
    """
    Отримує інформацію про IP-адресу через API ipwho.is.
    """
    url = f"https://ipwho.is/{ip}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()
    except httpx.HTTPError:
        return {}
