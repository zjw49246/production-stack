from typing import List
from fastapi import Request

G_REQ_ID = 0
def pick_server_for_request(request: Request, servers: List[str]) -> str:
    """Returns the target server's URL
    """
    global G_REQ_ID
    len_servers = len(servers)
    ret = servers[G_REQ_ID % len_servers]
    G_REQ_ID += 1
    return ret
