from typing import List, Optional
import numpy as np
from fastapi import Request

def round_robin_routing(servers: List[str]) -> str:
    if not hasattr(round_robin_routing, "REQ_ID"):
        round_robin_routing.REQ_ID = 0
    len_servers = len(servers)
    ret = servers[round_robin_routing.REQ_ID % len_servers]
    round_robin_routing.REQ_ID += 1
    return ret

def key_routing(servers: List[str], key: str) -> str:
    def pick_server_for_new_key(nservers, key_to_server_id):
        """Strawman solutions: finds the server with least users

        TODO: Could be improved -- based on server load
        """

        buckets = [0] * nservers
        for key in key_to_server_id:
            server_id = key_to_server_id[key]
            buckets[server_id] += 1

        return np.argmin(buckets)


    if not hasattr(key_routing, "KEY_TO_SERVER_ID"): 
        key_routing.KEY_TO_SERVER_ID = {}

    if key not in key_routing.KEY_TO_SERVER_ID:
        server_id = pick_server_for_new_key(
                len(servers), 
                key_routing.KEY_TO_SERVER_ID)
        key_routing.KEY_TO_SERVER_ID[key] = server_id
    else:
        server_id = key_routing.KEY_TO_SERVER_ID[key]

    print("Got server_id:", server_id)
    return servers[server_id]


def pick_server_for_request(
        request: Request, 
        servers: List[str], 
        routing_key: Optional[str] = None) -> str:
    """Returns the target server's URL
    """
    headers = request.headers
    if routing_key is None or routing_key not in request.headers:
        return round_robin_routing(servers)
    else:
        key = request.headers.get(routing_key)
        return key_routing(servers, key)
