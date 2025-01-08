from typing import List, Optional, Dict
import abc
import enum
from fastapi import Request

from engine_stats import EngineStats
from request_stats import RequestStats

from log import init_logger

logger = init_logger(__name__)

class RoutingLogic(enum.Enum):
    ROUND_ROBIN = "round-robin"
    SESSION_BASED = "session"

class RoutingInterface(metaclass = abc.ABCMeta):
    @abc.abstractmethod
    def route_request(
            self, 
            engine_urls: List[str],
            engine_stats: Dict[str, EngineStats],
            request_stats: Dict[str, RequestStats],
            request: Request) -> str:
        """
        Route the request to the appropriate engine URL

        Args:
            engine_urls (List[str]): The list of engine URLs
            engine_stats (Dict[str, EngineStats]): The engine stats indicating
                the 'physical' load of each engine
            request_stats (Dict[str, RequestStats]): The request stats
                indicating the request-level performance of each engine
            request (Request): The incoming request
        """
        raise NotImplementedError

class RoundRobinRouter(RoutingInterface):
    # TODO (ApostaC): when available engines in the engine_urls changes, the
    # algorithm may not be "perfectly" round-robin. 
    def __init__(self):
        self.req_id = 0

    def route_request(
            self, 
            engine_urls: List[str],
            engine_stats: Dict[str, EngineStats],
            request_stats: Dict[str, RequestStats],
            request: Request) -> str:
        """
        Route the request to the appropriate engine URL using a simple
        round-robin algorithm

        Args:
            engine_urls (List[str]): The list of engine URLs
            engine_stats (Dict[str, EngineStats]): The engine stats indicating
                the 'physical' load of each engine
            request_stats (Dict[str, RequestStats]): The request stats
                indicating the request-level performance of each engine
            request (Request): The incoming request
        """
        len_engines = len(engine_urls)
        ret = sorted(engine_urls)[self.req_id % len_engines]
        self.req_id += 1
        return ret

class SessionRouter(RoutingInterface):
    """
    Route the request to the appropriate engine URL based on the session key
    in the request headers
    """
    def __init__(self, session_key: str):
        self.key_to_server_id = {}
        self.session_key = session_key

    def _qps_routing(self, 
                     engine_urls: List[str], 
                     request_stats: Dict[str, RequestStats]) -> str:
        """
        Route the request to the appropriate engine URL based on the QPS of
        each engine

        Args:
            request_stats (Dict[str, RequestStats]): The request stats
                indicating the request-level performance of each engine
        """
        lowest_qps = float("inf")
        ret = None
        for url in engine_urls:
            if url not in request_stats:
                return url # This engine does not have any requests
            request_stat = request_stats[url]
            if request_stat.qps < lowest_qps:
                lowest_qps = request_stat.qps
                ret = url
        return ret

    def route_request(
            self, 
            engine_urls: List[str],
            engine_stats: Dict[str, EngineStats],
            request_stats: Dict[str, RequestStats],
            request: Request) -> str:
        """
        Route the request to the appropriate engine URL by the 'session id' in
        the request headers.
        If there is no session id in the request header, it will pick a server
        with lowest qps

        Args:
            engine_urls (List[str]): The list of engine URLs
            engine_stats (Dict[str, EngineStats]): The engine stats indicating
                the 'physical' load of each engine
            request_stats (Dict[str, RequestStats]): The request stats
                indicating the request-level performance of each engine
            request (Request): The incoming request
        """
        session_id = request.headers.get(self.session_key, None)
        logger.debug(f"Got session id: {session_id}")

        if session_id is None or session_id not in self.key_to_server_id:
            url = self._qps_routing(engine_urls, request_stats)
            if session_id is not None: 
                self.key_to_server_id[session_id] = url
        else:
            url = self.key_to_server_id[session_id]
        return url

def InitializeRoutingLogic(
        routing_logic: RoutingLogic,
        *args, **kwargs) -> RoutingInterface:
    """
    Initialize the routing logic based on the routing_logic string

    Args:
        routing_logic (str): The routing logic string
        **kwargs: The keyword arguments to pass to the routing

    Returns:
        RoutingInterface: The router object

    Raises:
        ValueError: If the routing_logic parameter is invalid
    """

    if routing_logic == RoutingLogic.ROUND_ROBIN:
        return RoundRobinRouter()
    elif routing_logic == RoutingLogic.SESSION_BASED:
        return SessionRouter(*args, **kwargs)
    else:
        raise ValueError("Invalid routing logic")
