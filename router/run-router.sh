#!/bin/bash
if [[ $# -ne 1 ]]; then
    echo "Usage $0 <router port>"
    exit 1
fi

python3 router.py --port $1 \
    --service-discovery k8s \
    --k8s-label-selector release=test \
    --routing-logic session \
    --session-key sessionId \

    #--backends http://localhost:8000/v1/chat/completions,http://localhost:8001/v1/chat/completions \
