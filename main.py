import re

from urllib.parse import unquote
from datetime import datetime, timezone, timedelta

from fastapi.middleware import Middleware
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from config import ALLOWED_IPS
from database.db import DbConnection


class IPFilterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_ips: list[str]):
        super().__init__(app)
        self.allowed_ips = allowed_ips

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        if client_ip not in self.allowed_ips:
            raise HTTPException(status_code=403, detail="Access forbidden")
        return await call_next(request)


app = FastAPI(
    middleware=[
        Middleware(IPFilterMiddleware, allowed_ips=ALLOWED_IPS)
    ]
)


@app.get("/call")
async def get_call(virtual_phone_number: str,
                   notification_time: str,
                   contact_phone_number: str):
    db_conn = DbConnection()

    virtual_phone_number = re.sub(r'\D', '', virtual_phone_number)
    virtual_phone_number = virtual_phone_number[-10:]

    notification_time = datetime.strptime(
        notification_time, "%Y-%m-%d %H:%M:%S.%f"
    ).replace(tzinfo=timezone.utc).astimezone(tz=timezone(timedelta(hours=3)))

    contact_phone_number = re.sub(r'\D', '', contact_phone_number)
    message = contact_phone_number[-6:]

    db_conn.add_message(virtual_phone_number=virtual_phone_number,
                        time_response=notification_time,
                        message=message,
                        marketplace='Ozon')


@app.get("/sms")
async def get_sms(virtual_phone_number: str,
                  notification_time: str,
                  contact_phone_number: str,
                  message: str):
    db_conn = DbConnection()

    virtual_phone_number = re.sub(r'\D', '', virtual_phone_number)
    virtual_phone_number = virtual_phone_number[-10:]

    notification_time = datetime.strptime(
        notification_time, "%Y-%m-%d %H:%M:%S.%f"
    ).replace(tzinfo=timezone.utc).astimezone(tz=timezone(timedelta(hours=3)))

    message = unquote(message)
    match = re.search(r'\b\d{6}\b', message)

    if match:
        message = match.group(0)

    if contact_phone_number == 'Wildberries':
        marketplace = 'WB'
    else:
        marketplace = None

    print(virtual_phone_number, notification_time, message, marketplace)
    db_conn.add_message(virtual_phone_number=virtual_phone_number,
                        time_response=notification_time,
                        message=message,
                        marketplace=marketplace)
