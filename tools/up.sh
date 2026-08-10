#!/usr/bin/env bash
# Bring up a DIVE stack for a worktree and seed it with the consistent test surface.
# Usage: tools/up.sh <worktree> [cpu|gpu]   (profile defaults to cpu)
set -euo pipefail

WT="${1:?usage: up.sh <worktree> [cpu|gpu]}"
PROFILE="${2:-cpu}"
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIVE="$(dirname "$KIT")/dive"
WTDIR="$DIVE/$WT"
[ -d "$WTDIR" ] || { echo "no worktree at $WTDIR" >&2; exit 1; }

echo "==> bring up stack for '$WT' (profile=$PROFILE)"
docker rm -f traefik autoheal >/dev/null 2>&1 || true
cd "$WTDIR"
[ -f .env ] || cp .env.default .env
if grep -q '^COMPOSE_PROJECT_NAME=' .env; then
  sed -i "s/^COMPOSE_PROJECT_NAME=.*/COMPOSE_PROJECT_NAME=$WT/" .env
else
  echo "COMPOSE_PROJECT_NAME=$WT" >> .env
fi
# Images are tagged with the same names as the published upstream ones, so compose reuses
# whatever is local and never notices a stale build. Rebuild only when an input is newer
# than the image: an unconditional --build costs ~5min and recreates containers every run.
stale() {
  local image="$1"; shift
  local created
  created="$(docker image inspect -f '{{.Created}}' "$image" 2>/dev/null)" || return 0
  created="$(date -d "$created" +%s)"
  local input
  for input in "$@"; do
    [ -e "$input" ] || continue
    [ "$(stat -c %Y "$input")" -gt "$created" ] && return 0
  done
  return 1
}

WORKER_IMAGE="kitware/viame-worker:cpu"
[ "$PROFILE" = gpu ] && WORKER_IMAGE="kitware/viame-worker:gpu"
BUILD_INPUTS=(server/pyproject.toml server/uv.lock docker/girder.Dockerfile
              docker/girder_worker.Dockerfile docker/girder_worker_gpu.Dockerfile)

UP_ARGS=()
if stale kitware/viame-web:latest "${BUILD_INPUTS[@]}" || stale "$WORKER_IMAGE" "${BUILD_INPUTS[@]}"; then
  echo "==> image is older than its build inputs; rebuilding"
  UP_ARGS+=(--build)
fi
docker compose --profile "$PROFILE" up -d "${UP_ARGS[@]}"

echo "==> wait for girder :8010"
for _ in $(seq 1 60); do
  [ "$(curl -s -m4 -o /dev/null -w '%{http_code}' http://localhost:8010/api/v1/system/version || true)" = 200 ] && break
  sleep 3
done

echo "==> seed"
uv run --with girder-client --no-project python "$KIT/tools/seed_datasets.py"
echo "==> done. Girder http://localhost:8010 (admin/letmein)"
echo "    client:  cd $WTDIR/client && VITE_PORT=3000 VITE_API_PROXY_TARGET=http://localhost:8010 npm run serve"
