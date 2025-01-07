from dataclasses import dataclass
from typing import Deque, Dict
from collections import deque

_global_request_stats_monitor = None

@dataclass
class RequestStats:
    # Number of queries per second
    qps: float

    # Average inter-token latency in seconds for each request
    inter_token_latency: float

    # Average time-to-first-token in seconds
    ttft: float

@dataclass
class SingleRequestRecord:
    """
    A single request record
    """
    # Global request ID
    request_id: str

    # Time when the request was created
    creation_time: float

    # Time when the first response token was received
    response_time: float

    # Time when the request was completed
    complete_time: float

    # Number of tokens in the prompt
    prompt_tokens: int

    # Number of tokens in the response
    generation_tokens: int

class RequestStatsMonitor:
    """
    Monitors the request statistics of all serving engines
    """
    # NOTE (ApostaC): Currently, QPS is calculated based on the number of 
    # arrived requests in the sliding window, but the inter_token_latency and
    # ttft are calculated based on the number of completed requests in the
    # sliding window. 
    def __init__(self, sliding_window_size: float):
        """
        Args:
            sliding_window_size: The size of the sliding window (in seconds) 
                to store the request statistics
        """
        self.sliding_window_size = sliding_window_size

        # Finished requests for each serving engine
        # The elements in the deque should be sorted by 'complete' time
        self.raw_request_history: Dict[str, deque[SingleRequestRecord]] = {}

        # The unfinished request for each serving engine
        # unfinished_requests[engine_url][request_id] = SingleRequestRecord
        self.unfinished_requests: Dict[str, Dict[str, SingleRequestRecord]] = {}

    def on_new_request(self, engine_url: str, request_id: str, timestamp: float):
        """
        Tell the monitor that a new request has been created.

        Args:
            engine_url: The URL of the serving engine
            request_id: The global request ID
            timestamp: the timestamp when the request was created
        """
        if engine_url not in self.unfinished_requests:
            self.unfinished_requests[engine_url] = {}

        self.unfinished_requests[engine_url][request_id] = SingleRequestRecord(
            request_id=request_id,
            creation_time=timestamp,
            response_time=0,
            complete_time=0,
            prompt_tokens=0,
            generation_tokens=0
        )

    def on_request_response(self, engine_url: str, request_id: str, timestamp: float):
        """
        Tell the monitor that a response token has been received for a request.

        Args:
            engine_url: The URL of the serving engine
            request_id: The global request ID
            timestamp: The timestamp when the response token was received
        """
        if engine_url not in self.unfinished_requests:
            return

        if request_id not in self.unfinished_requests[engine_url]:
            return

        if self.unfinished_requests[engine_url][request_id].response_time != 0:
            return

        self.unfinished_requests[engine_url][request_id].response_time = timestamp

    def on_request_complete(self, 
                            engine_url: str, 
                            request_id: str, 
                            timestamp: float,
                            prompt_tokens: int, 
                            generation_tokens: int):
        """
        Tell the monitor that a request has been completed.

        Args:
            engine_url: The URL of the serving engine
            request_id: The global request ID
            timestamp: The timestamp when the request was completed
            prompt_tokens: The number of tokens in the prompt
            generation_tokens: The number of tokens in the response
        """
        if engine_url not in self.unfinished_requests:
            return

        if request_id not in self.unfinished_requests[engine_url]:
            return

        record = self.unfinished_requests[engine_url][request_id]
        record.complete_time = timestamp
        record.prompt_tokens = prompt_tokens
        record.generation_tokens = generation_tokens

        # Update the raw request history
        if engine_url not in self.raw_request_history:
            self.raw_request_history[engine_url] = deque()
        self.raw_request_history[engine_url].append(record)

        # Remove the record from the unfinished requests
        self.unfinished_requests[engine_url].pop(request_id)
        

    def clear_outdated_requests(self, current_time: float):
        """
        Clear the outdated requests from the request history

        Args:
            current_time: The current time in seconds
        """
        for engine_url, records in self.raw_request_history.items():
            while len(records) > 0 and \
                    records[0].complete_time < \
                    current_time - self.sliding_window_size:
                records.popleft()

    def get_request_stats(
            self, 
            current_time: float,
        ) -> Dict[str, RequestStats]:
        """
        Get the request statistics for each serving engine

        Args:
            current_time: The current timestamp in seconds

        Returns:
            A dictionary where the key is the serving engine URL and the value
            is the request statistics for that engine.
            The TTFT and inter token latency will be -1 if there is no requests
            finished in the sliding window.
        """
        self.clear_outdated_requests(current_time)

        # Calculate the request statistics
        ret = {}
        for engine_url, records in self.raw_request_history.items():
            ttfts = []
            itls = []
            total_queries = 0
            for record in records:
                if current_time > record.creation_time >= current_time - self.sliding_window_size:
                    total_queries += 1
                if record.complete_time > current_time:
                    continue
                ttfts.append(record.response_time - record.creation_time)
                itls.append((record.complete_time - record.response_time) / record.generation_tokens)

            ret[engine_url] = RequestStats(
                qps = total_queries / self.sliding_window_size,
                inter_token_latency = sum(itls) / len(itls) if len(itls) > 0 else -1,
                ttft = sum(ttfts) / len(ttfts) if len(ttfts) > 0 else -1
            )

        return ret

def InitializeRequestStatsMonitor(sliding_window_size: float):
    """
    Initialize the global request statistics monitor

    Args:
        sliding_window_size: The size of the sliding window (in seconds) 
            to store the request

    Raises:
        ValueError: If the global request statistics monitor has been initialized
    """
    global _global_request_stats_monitor
    if _global_request_stats_monitor is not None:
        raise ValueError("The global request statistics monitor has been initialized")

    _global_request_stats_monitor = RequestStatsMonitor(sliding_window_size)
    return _global_request_stats_monitor

def GetRequestStatsMonitor():
    """
    Get the global request statistics monitor

    Returns:
        The global request statistics monitor

    Raises:
        ValueError: If the global request statistics monitor has not been initialized
    """
    global _global_request_stats_monitor
    if _global_request_stats_monitor is None:
        raise ValueError("The global request statistics monitor has not been initialized")

    return _global_request_stats_monitor

if __name__ == "__main__":
    import time
    monitor = InitializeRequestStatsMonitor(10)
    for i in range(20):
        monitor.on_new_request("engine1", f"request{i}", i)
        monitor.on_request_response("engine1", f"request{i}", i + 2)
        monitor.on_request_complete("engine1", f"request{i}", i + 4, 100, 40)

        monitor.on_new_request("engine2", f"request{i}", i)
        monitor.on_request_response("engine2", f"request{i}", i + 1)
        monitor.on_request_complete("engine2", f"request{i}", i + 2, 100, 40)

    print(monitor.get_request_stats(10))
    print(monitor.get_request_stats(20))
    print(monitor.get_request_stats(30))
    print(monitor.get_request_stats(40))
