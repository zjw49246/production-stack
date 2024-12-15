from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import httpx
import uvicorn
import argparse
import logging

from utils import validate_url
from logic import pick_server_for_request 

app = FastAPI()
logger = logging.getLogger("uvicorn")

# Define the backend server URL
BACKEND_SERVERS = []


GLOBAL_ARGS = None

async def process_request(request, backend_url):
    """
    Async generator to stream data from the backend server to the client.
    """
    client = httpx.AsyncClient()
    async with client.stream(
        method=request.method,
        url=backend_url,
        headers=dict(request.headers),
        content=await request.body(),
    ) as backend_response:

        # Pass response headers to the client
        yield backend_response.headers, backend_response.status_code

        # Stream response content
        async for chunk in backend_response.aiter_bytes():
            yield chunk

    await client.aclose()

@app.post("/chat/completions")
async def route_chat_completition(request: Request):
    """
    Route the incoming request to the backend server and stream the response back to the client.
    """
    #request_headers = request.headers
    #request_body = await request.body()
    #print(request_headers)
    #print(request_body)
    server_url = pick_server_for_request(request, BACKEND_SERVERS, GLOBAL_ARGS.routing_key)
    logger.info(f"Routing request to {server_url}")
    stream_generator = process_request(request, server_url)

    headers, status_code = await anext(stream_generator)
    logger.info(f"Response code: {status_code}")
    #print(status_code)

    return StreamingResponse(
            stream_generator,
            status_code=status_code,
            headers={key: value for key, value in headers.items() if key.lower() not in {"transfer-encoding"}},
        )


def parse_args():
    parser = argparse.ArgumentParser(description="Run the FastAPI app.")
    parser.add_argument("--backends", required=True, help="The URL of backend servers, separated by comma.")
    parser.add_argument("--host", default="0.0.0.0", help="The host to run the server on.")
    parser.add_argument("--port", type=int, default=8001, help="The port to run the server on.")
    parser.add_argument("--routing-key", type=str, default=None, help="The routing key in the header.")
    args = parser.parse_args()
    return args

def parse_backend_urls(args):
    urls = args.backends.split(",")
    for url in urls:
        if validate_url(url):
            BACKEND_SERVERS.append(url)
        else:
            logger.warning(f"Skipping invalid url: {url}")

if __name__ == "__main__":
    GLOBAL_ARGS = parse_args()
    parse_backend_urls(GLOBAL_ARGS)

    uvicorn.run(app, host=GLOBAL_ARGS.host, port=GLOBAL_ARGS.port)
