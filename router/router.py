from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import time
import httpx
import uvicorn
import argparse
import logging

from utils import validate_url
from routing_logic import InitializeRoutingLogic, RoutingLogic
from service_discovery import InitializeServiceDiscovery, GetServiceDiscovery, ServiceDiscoveryType
from request_stats import InitializeRequestStatsMonitor, GetRequestStatsMonitor
from engine_stats import InitializeEngineStatsScraper, GetEngineStatsScraper

app = FastAPI()
logger = logging.getLogger("uvicorn")

GLOBAL_ROUTER = None
REQUEST_ID = 0

# TODO: better request id system
# TODO: monitor the num tokens by adding the 'include_usage: True' to the request

async def process_request(request, backend_url, request_id, endpoint):
    """
    Async generator to stream data from the backend server to the client.
    """
    GetRequestStatsMonitor().on_new_request(
            backend_url,
            request_id,
            time.time())

    total_len = 0

    client = httpx.AsyncClient()
    async with client.stream(
        method=request.method,
        url=backend_url + endpoint, 
        headers=dict(request.headers),
        content=await request.body(),
    ) as backend_response:

        # Pass response headers to the client
        yield backend_response.headers, backend_response.status_code

        # Stream response content
        async for chunk in backend_response.aiter_bytes():
            GetRequestStatsMonitor().on_request_response(
                    backend_url,
                    request_id,
                    time.time(),)
            total_len += len(chunk)
            yield chunk

    await client.aclose()
    GetRequestStatsMonitor().on_request_complete(
            backend_url,
            request_id,
            time.time(),
            0, total_len)

@app.post("/chat/completions")
async def route_chat_completition(request: Request):
    """
    Route the incoming request to the backend server and stream the response back to the client.
    """
    global REQUEST_ID
    request_id = str(REQUEST_ID)
    REQUEST_ID += 1

    #request_headers = request.headers
    #request_body = await request.body()
    #print(request_headers)
    #print(request_body)
    engine_urls = GetServiceDiscovery().get_engine_urls()
    engine_stats = GetEngineStatsScraper().get_engine_stats()
    request_stats = GetRequestStatsMonitor().get_request_stats(time.time())

    server_url = GLOBAL_ROUTER.route_request(
            engine_urls,
            engine_stats,
            request_stats,
            request)


    logger.info(f"Routing request to {server_url}")
    stream_generator = process_request(
            request, 
            server_url, 
            request_id,
            endpoint = "/v1/chat/completions")

    headers, status_code = await anext(stream_generator)
    logger.info(f"Response code: {status_code}")
    #print(status_code)

    return StreamingResponse(
            stream_generator,
            status_code=status_code,
            headers={key: value for key, value in headers.items() if key.lower() not in {"transfer-encoding"}},
        )


def validate_args(args):
    if args.service_discovery not in ["static", "k8s"]:
        raise ValueError(f"Invalid service discovery type: {args.service_discovery}")

    if args.routing_logic not in ["roundrobin", "session"]:
        raise ValueError(f"Invalid routing logic: {args.routing_logic}")

    if args.service_discovery == "static" and args.static_backends is None:
        raise ValueError("Static backends must be provided when using static service discovery.")

    if args.service_discovery == "k8s" and args.k8s_port is None:
        raise ValueError("K8s port must be provided when using K8s service discovery.")

    if args.routing_logic == "session" and args.session_key is None:
        raise ValueError("Session key must be provided when using session routing logic.")

def parse_args():
    parser = argparse.ArgumentParser(description="Run the FastAPI app.")
    parser.add_argument("--host", default="0.0.0.0", help="The host to run the server on.")
    parser.add_argument("--port", type=int, default=8001, help="The port to run the server on.")

    # Service discovery
    parser.add_argument("--service-discovery", required=True, 
                        help = "The service discovery type. Options: static, k8s")
    parser.add_argument("--static-backends", type=str, default=None, 
                        help="The urls of static backends, separeted by comma."
                             "E.g., http://localhost:8000,http://localhost:8001")
    parser.add_argument("--k8s-port", type=int, default=8000, 
                        help="The port of vLLM processes when using K8s service discovery.")
    parser.add_argument("--k8s-namespace", type=str, default="default",
                        help="The namespace of vLLM pods when using K8s service discovery.")
    parser.add_argument("--k8s-label-selector", type=str, default="",
                        help="The label selector to filter vLLM pods when using K8s service discovery.")

    # Routing logic
    parser.add_argument("--routing-logic", type=str, required=True, 
                        help="The routing logic to use, Options: roundrobin, session")
    parser.add_argument("--session-key", type=str, default=None,
                        help="The key (in the header) to identify a session.")

    # Monitoring
    parser.add_argument("--engine-stats-interval", type=int, default=30,
                        help="The interval in seconds to scrape engine statistics.")
    parser.add_argument("--request-stats-window", type=int, default=60,
                        help="The sliding window seconds to compute request statistics.")

    args = parser.parse_args()
    validate_args(args)
    return args

def parse_backend_urls(args):
    urls = args.backends.split(",")
    backend_urls = []
    for url in urls:
        if validate_url(url):
            backend_urls.append(url)
        else:
            logger.warning(f"Skipping invalid url: {url}")
    return backend_urls

def InitializeAll(args):
    if args.service_discovery == "static":
        InitializeServiceDiscovery(ServiceDiscoveryType.STATIC, 
                                   backend_urls = parse_backend_urls(args))
    elif args.service_discovery == "k8s":
        InitializeServiceDiscovery(ServiceDiscoveryType.K8S, 
                                   namespace = args.k8s_namespace, 
                                   port = args.k8s_port, 
                                   label_selector = args.k8s_label_selector)
    else:
        raise ValueError(f"Invalid service discovery type: {args.service_discovery}")

    InitializeEngineStatsScraper(30)
    InitializeRequestStatsMonitor(60)

    global GLOBAL_ROUTER
    if args.routing_logic == "roundrobin":
        GLOBAL_ROUTER = InitializeRoutingLogic(
                RoutingLogic.ROUND_ROBIN
        )
    elif args.routing_logic == "session":
        GLOBAL_ROUTER = InitializeRoutingLogic(
                RoutingLogic.SESSION_BASED,
                session_key = args.session_key
        )
    else:
        raise ValueError(f"Invalid routing logic: {args.routing_logic}")
    
if __name__ == "__main__":
    args = parse_args()
    #parse_backend_urls(GLOBAL_ARGS)

    InitializeAll(args)

    uvicorn.run(app, host=args.host, port=args.port)
