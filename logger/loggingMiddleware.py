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
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.log_service_url = os.getenv("LOG_SERVICE_URL")
        self.service_name = os.getenv("SERVICE_NAME", "default_service")
        if not self.log_service_url:
            print("LOG_SERVICE_URL is not set")

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Generate traceId if not present
        traceId = request.headers.get("traceId")
        if traceId is None:
            traceId = str(uuid.uuid4())
        request.state.traceId = traceId

        # Capture the request body asynchronously
        request_body = await request.body()
        request_body_str = request_body.decode('utf-8')

        # Record the start time in a string format
        start_time_str = datetime.fromtimestamp(start_time, tz=timezone.utc).isoformat(timespec='seconds') 

        # Prepare the request log data
        request_log = {
            "traceId": traceId,
            "remote_ip": request.client.host,
            "host": request.url.hostname,
            "method": request.method,
            "uri": str(request.url.path),
            "user_agent": request.headers.get("User-Agent"),
            "requestHeaders": dict(request.headers),
            "requestBody": request_body_str,
            "startTime": start_time_str,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec='seconds') 
        }

        # Prepare the request log structure
        request_log_data = {
            "service": "querier",
            "stage": "START",  # or "development" depending on your environment
            "type": "API",
            "data": request_log,
            "traceId": traceId,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec='seconds') 
        }

        # Send the request log asynchronously
        if self.log_service_url:
            asyncio.create_task(self.send_log(request_log_data))
        else:
            print("Log service URL is missing")

        # Call the next middleware or request handler
        response = await call_next(request)

        # Capture the response body asynchronously
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        # Measure the time taken
        end_time = time.time()
        duration = end_time - start_time
        end_time_str = datetime.fromtimestamp(end_time, tz=timezone.utc).isoformat()

        # Prepare the response log data
        end_time_str = datetime.fromtimestamp(end_time, tz=timezone.utc).isoformat(timespec='seconds') 

        # Prepare the response log data
        response_log = {
            "traceId": traceId,
            "status": response.status_code,
            "responseHeaders": dict(response.headers),
            "responseBody": response_body.decode('utf-8'),
            "startTime": start_time_str,
            "endTime": end_time_str,
            "latency": f"{duration:.6f} seconds",
            "timestamp": datetime.now(timezone.utc).isoformat(timespec='seconds') 
        }

        # Prepare the response log structure
        response_log_data = {
            "service": "querier",
            "stage": "END",  # or "development" depending on your environment
            "type": "API",
            "data": response_log,
            "traceId": traceId,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec='seconds')
        }

        # Send the response log asynchronously
        if self.log_service_url:
            asyncio.create_task(self.send_log(response_log_data))
        else:
            print("Log service URL is missing")

        # Return the original response
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
                if response.status_code != 200:
                    print(f"Log service returned status code {response.text}")
            except Exception as e:
                print(f"Error posting log data: {e}")
