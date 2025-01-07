from typing import List, Dict, Optional
import threading
import abc
from kubernetes import client, config, watch


from log import init_logger

logger = init_logger(__name__)

class ServiceDiscovery(metaclass = abc.ABCMeta):
    @abc.abstractmethod
    def get_engine_urls(self) -> List[str]:
        """
        Get the URLs of the serving engines that are available for
        querying.

        Returns:
            a list of engine URLs
        """
        pass


class StaticServiceDiscovery(ServiceDiscovery):
    def __init__(self, urls: List[str]):
        self.urls = urls

    def get_engine_urls(self) -> List[str]:
        return self.urls


class K8sServiceDiscovery(ServiceDiscovery):
    def __init__(self, namespace: str, port: str, label_selector = None):
        self.namespace = namespace
        self.port = port
        self.available_engines: Dict[str, str] = {}
        self.available_engines_lock = threading.Lock()
        self.label_selector = label_selector

        # Init kubernetes watcher
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()

        self.k8s_api = client.CoreV1Api()
        self.k8s_watcher = watch.Watch()

        # Start watching engines
        self.watcher_thread = threading.Thread(
                target=self._watch_engines,
                daemon=True)
        self.watcher_thread.start()

    def _watch_engines(self):
        # TODO (ApostaC): Add error handling

        for event in self.k8s_watcher.stream(
            self.k8s_api.list_namespaced_pod,
            namespace=self.namespace,
            label_selector=self.label_selector,
        ):
            pod = event["object"]
            event_type = event["type"]
            pod_name = pod.metadata.name
            pod_ip = pod.status.pod_ip
            self._on_engine_update(pod_name, pod_ip, event_type)

    def _on_engine_update(
            self, 
            engine_name: str,
            engine_ip: Optional[str],
            event: str
        ) -> None:
        if event == "ADDED":
            if engine_ip is None:
                return

            with self.available_engines_lock:
                self.available_engines[engine_name] = engine_ip

        elif event == "DELETED":
            if engine_name not in self.available_engines:
                return

            with self.available_engines_lock:
                del self.available_engines[engine_name]
        
        elif event == "MODIFIED":
            if engine_ip is None:
                return

            with self.available_engines_lock:
                self.available_engines[engine_name] = engine_ip

    def get_engine_urls(self) -> List[str]:
        # Use Kubernetes API to get the engine URLs
        with self.available_engines_lock:
            return [
                f"http://{ip}:{self.port}" for ip in self.available_engines.values()
            ]

if __name__ == "__main__":
    # Test the service discovery
    k8s_sd = K8sServiceDiscovery("default", 8000, "release=test")

    import time
    time.sleep(1)
    urls = k8s_sd.get_engine_urls()
    print(urls)
