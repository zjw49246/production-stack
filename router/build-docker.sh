commit_id=$(git reflog | cut -d' ' -f1 | head -n 1)
echo "Commit id is: $commit_id"
docker build \
	--build-arg COMMIT_ID=$commit_id . \
	--tag apostacyh/lmcache-router:latest
