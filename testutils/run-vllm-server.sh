#!/bin/bash
if [[ $# -ne 1 ]]; then
    echo "Usage $0 <port>"
    exit 1
fi

vllm serve mistralai/Mistral-7B-Instruct-v0.2 --gpu-memory-utilization 0.4 --max-model-len 8192 -q fp8 --port $1
