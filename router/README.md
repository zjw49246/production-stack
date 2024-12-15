# Router

## Build docker image

```bash
docker build -t apostacyh/lmcache-router:test .
```

## Run docker image

Example docker run code

```bash
sudo docker run --network host apostacyh/lmcache-router:test \
    --host 0.0.0.0 --port 9090 \
    --routing-key my_user_id \
    --backends http://<serving engine url1>/v1/chat/completions,http://<serving engine url2>/v1/chat/completions
```
