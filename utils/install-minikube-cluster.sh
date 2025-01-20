#!/bin/bash
set -e

# Install kubectl and helm
bash ./install-kubectl.sh
bash ./install-helm.sh

# Install minikube
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64
echo "net.core.bpf_jit_harden=0" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Install nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker

# Start cluster
sudo minikube start --driver docker --container-runtime docker --gpus all --force
