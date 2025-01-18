ps -aux | grep "python3 ./fake-openai" | awk '{print $2}' | xargs kill -9
