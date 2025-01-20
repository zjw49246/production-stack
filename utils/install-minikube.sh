#!/bin/bash
set -e
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64
echo "net.core.bpf_jit_harden=0" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
sudo minikube start --driver docker --container-runtime docker --gpus all --force
