# utils/ip.py
from fastapi import Request

def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    return forwarded_for.split(",")[0] if forwarded_for else request.client.host
