# Helm chart

## Prerequisites

### A running K8s environment

See [this doc](https://gd41ffv7q3z.larksuite.com/wiki/Xtj7wer5Ni9GXZkDEnfubXf0s7g?from=from_copylink) (internal doc link)

### Create PersistentVolume (PV) in K8s (Optional)

__NOTE__: This is optional because this helm chart is using `standard` storage class and the k8s cluster can dynamically create PVs for this storage class.

If you want to create your own PV, follow the instructions below:

Replace `<SIZE OF THE PV>` and `<HOST PATH ON YOUR MACHINE>` in the following yaml and save it as `pv.yaml`
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

Run the following command to create the PV
```bash
kubectl apply -f pv.yaml
```


## To run it

0. Go to the directory of this helm chart

1. Have your customized configs stored in `values-customized.yaml`, for example

```yaml
image:
  command: ["vllm", "serve", "mistralai/Mistral-7B-Instruct-v0.2", "--host", "0.0.0.0", "--port", "8000"]
  env:
    - name: HF_TOKEN
      value: <YOUR HUGGING FACE TOKEN>

gpuModels:
  - "<THE NVIDIA GPU NAME>"
```

2. run `helm upgrade --install test-vllm . -f values-customized.yaml`

## To stop

run `helm uninstall test-vllm`
