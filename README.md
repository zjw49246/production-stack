# LMStack

This project provides a reference implementation on how to build a inference stack on top of vLLM, including the following components:

- **Grafana Dashboard**: Visualizes key LLM serving metrics.
- **Helm Chart**: Deploys vLLM services in Kubernetes environments.
- **Router**: Directs requests to appropriate backends based on routing keys or session IDs.
- **Tests**: Multi-round testing framework to ensure system functionality.

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

### Configuration

- Data source: Prometheus
- Refresh interval: Automatic

## Helm Chart

### Prerequisites

- A running Kubernetes (K8s) environment
- (Optional) PersistentVolume (PV) setup

### Setup

#### Creating a PersistentVolume (Optional)

If dynamic provisioning is not enabled, you can manually create a PV:

1. Replace `<SIZE OF THE PV>` and `<HOST PATH ON YOUR MACHINE>` in the following YAML file:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: test-vllm-pv
spec:
  capacity:
    storage: <SIZE OF THE PV, EX: 100Gi>
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: standard
  hostPath:
    path: <HOST PATH ON YOUR MACHINE>
```

2. Apply the configuration:

```bash
kubectl apply -f pv.yaml
```

#### Deployment

1. Store your custom configurations in `values-customized.yaml`. Example:

```yaml
image:
  command: ["vllm", "serve", "mistralai/Mistral-7B-Instruct-v0.2", "--host", "0.0.0.0", "--port", "8000"]
  env:
    - name: HF_TOKEN
      value: <YOUR HUGGING FACE TOKEN>

gpuModels:
  - "<THE NVIDIA GPU NAME>"
```

2. Deploy the Helm chart:

```bash
helm upgrade --install test-vllm . -f values-customized.yaml
```

#### Uninstall

```bash
helm uninstall test-vllm
```

### Notes

- The HF\_HOME directory is hard-coded to `/data` as the PV is mounted there.

## Router

### Overview

The router ensures efficient request distribution among backends. It supports:

- **Routing by User ID**: Uses a `routing-key` to direct requests.
- **Session-Based Routing** (TODO): Maps new session IDs to backends using a hash function and cleans up stale sessions.

### Build and Run

#### Build Docker Image

```bash
docker build -t apostacyh/lmcache-router:test .
```

#### Run Docker Image

```bash
sudo docker run --network host apostacyh/lmcache-router:test \
    --host 0.0.0.0 --port 9090 \
    --routing-key my_user_id \
    --backends http://<serving engine url1>/v1/chat/completions,http://<serving engine url2>/v1/chat/completions
```

### TODOs

- Implement session-based routing.
- Add session cleanup logic to manage active sessions.

## Tests

The project includes a multi-round test framework to validate functionality across all components.

## Contributing

Contributions are welcome! Please follow the standard GitHub flow:

1. Fork the repository.
2. Create a feature branch.
3. Submit a pull request with detailed descriptions.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

For any issues or questions, feel free to open an issue or contact the maintainers.

