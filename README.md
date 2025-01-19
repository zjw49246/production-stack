# LMStack


This project provides a reference implementation on how to build an inference stack on top of vLLM, including the following components:

- **Helm Chart**: Deploys vLLM services in Kubernetes environments.
- **Grafana Dashboard**: Visualizes key LLM serving metrics for monitoring.

Inside the stack, there are the following key parts:
- **Backend**: The vLLM engines that runs different LLMs
- **Router**: Directs requests to appropriate backends based on routing keys or session IDs to maximize KV cache reuse.

 <img src="https://github.com/user-attachments/assets/ffbdb2de-0dce-46cf-bc07-c4057b35ad7f" alt="Architecture of the stack" width="800"/>

## Helm Chart

### Prerequisites

- A running Kubernetes (K8s) environment with GPUs ([Tutorial](https://minikube.sigs.k8s.io/docs/tutorials/nvidia/))


### Deployment

1. Store your custom configurations in `values-customized.yaml`. Example:
```yaml
servingEngineSpec:
  modelSpec:
  - name: "opt125m"
    replicaCount: 2

    requestCPU: 6
    requestMemory: "16Gi"
    requestGPU: 1

    pvcStorage: "10Gi"

    image:
      # -- Image repository
      repository: "vllm/vllm-openai"
      # -- Image tag
      tag: "latest"

      command: ["vllm", "serve", "facebook/opt-125m", "--host", "0.0.0.0", "--port", "8000",
                "--disable-log-requests"]

routerSpec:
  extraArgs:
    - "--routing-logic"
    - "roundrobin"
```

3. Deploy the Helm chart:

```bash
helm install lmstack . -f values-customized.yaml
```

#### Uninstall

```bash
helm uninstall lmstack
```


## Grafana Dashboard

### Features

The Grafana dashboard provides the following insights:


1. **Available vLLM Instances**: Displays the number of healthy instances.
2. **Request Latency Distribution**: Visualizes end-to-end request latency.
3. **Time-to-First-Token (TTFT) Distribution**: Monitors response times for token generation.
4. **Number of Running Requests**: Tracks the number of active requests per instance.
5. **Number of Pending Requests**: Tracks requests waiting to be processed.
6. **GPU KV Usage Percent**: Monitors GPU KV cache usage.
7. **GPU KV Cache Hit Rate**: Displays the hit rate for the GPU KV cache.

 <img src="https://github.com/user-attachments/assets/225feb01-ac0f-4bf9-9da3-7bf955b2aa56" alt="Grafana dashboard to monitor the deployment" width="500"/>

### Configuration

See the details in `observability/README.md`

## Router

### Overview

The router ensures efficient request distribution among backends. It supports:

- Routing to endpoints that run different models
- Exporting observability metrics for each serving engine instance, including QPS, time-to-first-token (TTFT), number of pending/running/finished requests, and uptime
- Automatic service discovery and fault tolerance by Kubernetes API
- Multiple different routing algorithms
  - Round-robin routing
  - Session-ID based routing
  - (WIP) prefix-aware routing


## Contributing

Contributions are welcome! Please follow the standard GitHub flow:

1. Fork the repository.
2. Create a feature branch.
3. Submit a pull request with detailed descriptions.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

For any issues or questions, feel free to open an issue or contact the maintainers.

