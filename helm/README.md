# Helm chart

## To run it

1. modify the `gpuModels` in the values.yaml
2. run `helm upgrade --install test-vllm . -f values.yaml`

## To stop

run `helm uninstall test-vllm`
