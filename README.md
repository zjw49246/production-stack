# LLMStack: reference stack for production vLLM deployment 


**LLMStack** project provides a reference implementation on how to build an inference stack on top of vLLM, which allows you to:

- 🚀 Scale from single vLLM instance to distributed vLLM deployment without changing any application code
- 💻 Monitor the  through a web dashboard
- 😄 Enjoy the performance benefits brought by request routing and KV cache offloading

## Latest News:

- 🔥 LLMStack is released! Checkout our [release blogs](https://blog.lmcache.ai/2025-01-22-stack-release/) [01-22-2025]

## Architecture

The stack is set up using [Helm](https://helm.sh/docs/), and contains the following key parts:

- **Serving engine**: The vLLM engines that run different LLMs
- **Request router**: Directs requests to appropriate backends based on routing keys or session IDs to maximize KV cache reuse.
- **Observability stack**: monitors the metrics of the backends through [Prometheus](https://github.com/prometheus/prometheus) + [Grafana](https://grafana.com/)

 <img src="https://github.com/user-attachments/assets/ffbdb2de-0dce-46cf-bc07-c4057b35ad7f" alt="Architecture of the stack" width="800"/>

## Deploying LLMStack via Helm

### Prerequisites

- A running Kubernetes (K8s) environment with GPUs
  - Run `cd utils && bash install-minikube-cluster.sh`
  - Or: [tutorial](https://minikube.sigs.k8s.io/docs/tutorials/nvidia/)


### Deployment

1. Store your custom configurations in `values-customized.yaml`. Example:
```yaml
servingEngineSpec:
  modelSpec:
  - name: "opt125m"
    repository: "lmcache/vllm-openai"
    tag: "latest"
    modelURL: "facebook/opt-125m"

    replicaCount: 1

    requestCPU: 6
    requestMemory: "16Gi"
    requestGPU: 1

    pvcStorage: "10Gi"
```

2. Deploy the Helm chart:

```bash
sudo helm repo add llmstack-repo https://lmcache.github.io/helm/
sudo helm install llmstack llmstack-repo/vllm-stack -f values-customized.yaml
```

For more information about customizing the helm chart, please refer to [values.yaml](https://github.com/vllm-project/production-stack/blob/main/helm/values.yaml) and our [tutorials](https://github.com/vllm-project/production-stack/tree/main/tutorials).

### Validate the installation

**Monitor the status of the deployment**: 
The following command can be used to monitor the deployment
```bash
sudo kubectl get pods
```

You should be able to see outputs like this:
```
NAME                                               READY   STATUS              RESTARTS   AGE
llmstack-deployment-router-859d8fb668-2x2b7        1/1     Running             0          5s
llmstack-opt125m-deployment-vllm-84dfc9bd7-vb9bs   0/1     ContainerCreating   0          5s
```

Now please wait until all the pods turned into READY the second row to turn into `Running` and `READY 1/1` states.
```
NAME                                               READY   STATUS    RESTARTS   AGE
llmstack-deployment-router-859d8fb668-2x2b7        1/1     Running   0          2m38s
llmstack-opt125m-deployment-vllm-84dfc9bd7-vb9bs   1/1     Running   0          2m38s
```

_Note_: it takes some time to download the docker images and the LLM weights. You might need to wait for it to be ready.

### Send a query to the stack via OpenAI API:

The stack provides the same [**OpenAI API interface**](https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html?ref=blog.mozilla.ai#openai-compatible-server) as vLLM, and can be accessed through kubernetes service.

Follow the instructions below to send an example query to the OpenAI endpoint:

1. forward the service port to the host machine (port 30080):
```bash
sudo kubectl port-forward svc/llmstack-router-service 30080:80
```

2. open a new terminal, and curl the endpoint on the host machine
```bash
curl -o- http://localhost:30080/models
```

3. You should see outputs like
```json
{
  "object": "list",
  "data": [
    {
      "id": "facebook/opt-125m",
      "object": "model",
      "created": 1737428424,
      "owned_by": "vllm",
      "root": null
    }
  ]
}
```

The available endpoints are:
```text
/health, Methods: GET
/tokenize, Methods: POST
/detokenize, Methods: POST
/models, Methods: GET
/version, Methods: GET
/chat/completions, Methods: POST
/completions, Methods: POST
/embeddings, Methods: POST
```

#### Uninstall

```bash
sudo helm uninstall llmstack
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

