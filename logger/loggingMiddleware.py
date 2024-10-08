import os
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import httpx
import asyncio
from datetime import datetime, timezone

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, service_name: str):
        super().__init__(app)
        self.log_service_url = os.getenv("LOG_SERVICE_URL") + "/log"
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        traceId = request.headers.get("traceId")
        if traceId is None:
            traceId = str(uuid.uuid4())
        request.state.traceId = traceId

        try:
            request_body = await request.body()
            request_body_str = request_body.decode('utf-8')
        except Exception:
            request_body_str = None

        start_time_str = datetime.fromtimestamp(start_time, tz=timezone.utc).isoformat(timespec='seconds') 

        request_log = {
            "traceId": traceId,
            "remote_ip": getattr(request.client, 'host', None),
            "host": request.url.hostname,
            "method": request.method,
            "uri": str(request.url.path),
            "user_agent": request.headers.get("User-Agent"),
            "requestHeaders": dict(request.headers) if request.headers else None,
            "requestBody": request_body_str,
            "startTime": start_time_str,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec='seconds') 
        }

        request_log_data = {
            "service": self.service_name,
            "stage": "START",  
            "type": "API",
            "data": request_log,
            "traceId": traceId,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec='seconds') 
        }

        if self.log_service_url:
            asyncio.create_task(self.send_log(request_log_data))
        else:
            print("Log service URL is missing")

        response = await call_next(request)

        response_body = b""
        try:
            async for chunk in response.body_iterator:
                response_body += chunk
        except Exception:
            response_body = b""

        end_time = time.time()
        duration = end_time - start_time
        end_time_str = datetime.fromtimestamp(end_time, tz=timezone.utc).isoformat(timespec='seconds') 

        response_log = {
            "traceId": traceId,
            "status": response.status_code,
            "responseHeaders": dict(response.headers) if response.headers else None,
            "responseBody": response_body.decode('utf-8', errors='ignore'),
            "startTime": start_time_str,
            "endTime": end_time_str,
            "latency": f"{duration:.6f} seconds",
            "timestamp": datetime.now(timezone.utc).isoformat(timespec='seconds')
        }

        response_log_data = {
            "service": self.service_name,
            "stage": "END",
            "type": "API",
            "data": response_log,
            "traceId": traceId,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec='seconds')
        }

        if self.log_service_url:
            asyncio.create_task(self.send_log(response_log_data))
        else:
            print("Log service URL is missing")

        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )

    async def send_log(self, log_data):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.log_service_url, json=log_data)
            except httpx.HTTPStatusError as http_err:
                print(
                    f"HTTP error occurred while posting log data: {http_err.response.status_code} "
                    f"({http_err.response.reason_phrase}) - {http_err.response.text}"
                )
            except httpx.RequestError as req_err:
                print(f"Request error occurred while posting log data: {str(req_err)}")
            except Exception as e:
                print(f"Unexpected error posting log data: {str(e)}")
